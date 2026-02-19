from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Callable

import discord
import discord.ext.voice_recv as voice_recv


@dataclass
class UserAudioBuffer:
    chunks: list[bytes] = field(default_factory=list)
    last_seen: float = 0.0

    def append(self, pcm: bytes) -> None:
        self.chunks.append(pcm)
        self.last_seen = time.monotonic()

    def flush(self) -> bytes:
        if not self.chunks:
            return b""
        data = b"".join(self.chunks)
        self.chunks.clear()
        return data


class VoiceReceiveSession:
    """Collect per-user PCM and emit utterances after short silence."""

    def __init__(
        self,
        *,
        guild: discord.Guild,
        on_utterance: Callable[[str, bytes], "asyncio.Future[None] | asyncio.Task[None] | None"],
        silence_seconds: float = 0.8,
        min_pcm_bytes: int = 9600,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self.guild = guild
        self._on_utterance = on_utterance
        self._silence_seconds = silence_seconds
        self._min_pcm_bytes = min_pcm_bytes
        self._buffers: dict[int, UserAudioBuffer] = {}
        self._sink: voice_recv.BasicSink | None = None
        self._loop_task: asyncio.Task[None] | None = None
        self._running = False

    async def start(self, voice_client: voice_recv.VoiceRecvClient) -> None:
        self._running = True
        self._sink = voice_recv.BasicSink(self._on_voice_data, decode=True)
        voice_client.listen(self._sink)
        self._loop_task = asyncio.create_task(self._flush_loop())
        self._logger.info("Voice receive session started (guild=%s)", self.guild.id)

    async def stop(self, voice_client: voice_recv.VoiceRecvClient) -> None:
        self._running = False
        if self._loop_task:
            self._loop_task.cancel()
            try:
                await self._loop_task
            except asyncio.CancelledError:
                pass
        if voice_client.is_listening():
            voice_client.stop_listening()
        await self._flush_all()
        self._logger.info("Voice receive session stopped (guild=%s)", self.guild.id)

    def _on_voice_data(self, user: discord.Member | None, data: voice_recv.VoiceData) -> None:
        if user is None or user.bot:
            return
        if not data.pcm:
            return
        buf = self._buffers.setdefault(user.id, UserAudioBuffer())
        buf.append(data.pcm)

    async def _flush_loop(self) -> None:
        while self._running:
            await asyncio.sleep(0.2)
            now = time.monotonic()
            for user_id, buf in list(self._buffers.items()):
                if not buf.chunks:
                    continue
                if now - buf.last_seen < self._silence_seconds:
                    continue
                pcm = buf.flush()
                if len(pcm) < self._min_pcm_bytes:
                    continue
                member = self.guild.get_member(user_id)
                if member is None:
                    continue
                self._logger.info("Voice utterance captured user=%s bytes=%s", member.display_name, len(pcm))
                result = self._on_utterance(member.display_name, pcm)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)

    async def _flush_all(self) -> None:
        for user_id, buf in list(self._buffers.items()):
            pcm = buf.flush()
            if len(pcm) < self._min_pcm_bytes:
                continue
            member = self.guild.get_member(user_id)
            if member is None:
                continue
            result = self._on_utterance(member.display_name, pcm)
            if asyncio.iscoroutine(result):
                await result
