from __future__ import annotations

import asyncio
import logging

import discord
import discord.ext.voice_recv as voice_recv

from ai.gpt import GPTResponder
from audio.player import VoicePlayer
from audio.tts import VoiceVoxTTS
from audio.vad import VADSegmenter
from audio.wav import pcm16k_mono_to_wav, pcm48k_stereo_to_pcm16k_mono
from audio.whisper import WhisperTranscriber
from bot.voice_receive import VoiceReceiveSession
from history.discord_history import DiscordHistoryStore
from history.permanent_memory import PermanentMemoryStore


class VoiceHandler:
    def __init__(
        self,
        vad: VADSegmenter,
        whisper: WhisperTranscriber,
        gpt: GPTResponder,
        tts: VoiceVoxTTS,
        player: VoicePlayer,
        history: DiscordHistoryStore,
        permanent_memory: PermanentMemoryStore,
    ) -> None:
        self._logger = logging.getLogger(__name__)
        self._vad = vad
        self._whisper = whisper
        self._gpt = gpt
        self._tts = tts
        self._player = player
        self._history = history
        self._permanent_memory = permanent_memory
        self.character_prompt = "タメ口でフレンドリーに話す。"
        self._playback_lock = asyncio.Lock()
        self._sessions: dict[int, VoiceReceiveSession] = {}

    async def join(self, interaction: discord.Interaction, history_channel: discord.TextChannel | None = None) -> str:
        if not interaction.user or not isinstance(interaction.user, discord.Member):
            return "VC接続に失敗しました（ユーザー情報が取得できません）。"

        voice_state = interaction.user.voice
        if not voice_state or not voice_state.channel:
            return "先にVCへ参加してください。"

        channel = voice_state.channel
        if interaction.guild and interaction.guild.voice_client:
            return "すでにVCへ接続中です。"

        voice_client = await channel.connect(cls=voice_recv.VoiceRecvClient)
        if not interaction.guild:
            return f"{channel.name} に参加しました。"

        if history_channel is None:
            return (
                f"{channel.name} に参加しましたが、HISTORY_CHANNEL_ID のチャンネルが見つからないため"
                "音声処理を開始できません。"
            )

        if isinstance(voice_client, voice_recv.VoiceRecvClient):
            await self.start_listening(interaction.guild, history_channel, voice_client)
            return f"{channel.name} に参加しました。音声リスニングを開始しました。"

        return f"{channel.name} に参加しましたが、音声受信クライアントの初期化に失敗しました。"

    async def leave(self, interaction: discord.Interaction) -> str:
        if interaction.guild and interaction.guild.voice_client:
            await self.stop_listening(interaction.guild)
            await interaction.guild.voice_client.disconnect(force=True)
            return "VCから退出しました。"
        return "VCに接続していません。"

    async def start_listening(
        self,
        guild: discord.Guild,
        history_channel: discord.TextChannel,
        voice_client: voice_recv.VoiceRecvClient | None = None,
    ) -> None:
        if guild.id in self._sessions:
            return
        vc = voice_client or guild.voice_client
        if not isinstance(vc, voice_recv.VoiceRecvClient):
            self._logger.warning("Voice client is not VoiceRecvClient; voice receive disabled.")
            return

        async def _on_utterance(user_display_name: str, pcm48_stereo: bytes) -> None:
            pcm16 = pcm48k_stereo_to_pcm16k_mono(pcm48_stereo)
            wav = pcm16k_mono_to_wav(pcm16)
            await self.process_user_audio(
                guild=guild,
                history_channel=history_channel,
                user_display_name=user_display_name,
                pcm16_mono=pcm16,
                wav_bytes=wav,
            )

        session = VoiceReceiveSession(guild=guild, on_utterance=_on_utterance)
        await session.start(vc)
        self._sessions[guild.id] = session
        self._logger.info("Voice receive started for guild=%s", guild.id)

    async def stop_listening(self, guild: discord.Guild) -> None:
        session = self._sessions.pop(guild.id, None)
        vc = guild.voice_client
        if session and isinstance(vc, voice_recv.VoiceRecvClient):
            await session.stop(vc)
            self._logger.info("Voice receive stopped for guild=%s", guild.id)

    async def process_user_audio(
        self,
        *,
        guild: discord.Guild,
        history_channel: discord.TextChannel,
        user_display_name: str,
        pcm16_mono: bytes,
        wav_bytes: bytes,
    ) -> str:
        try:
            if not self._vad.has_speech(pcm16_mono):
                return ""

            transcript = self._whisper.transcribe_ja(wav_bytes)
            if not transcript:
                return ""

            await self._history.append_line(history_channel, user_display_name, transcript)
            history_lines = await self._history.fetch_recent_lines(history_channel)
            memory_text = self._permanent_memory.cache.to_prompt_text()
            reply = self._gpt.generate_reply(
                user_name=user_display_name,
                transcript=transcript,
                history_lines=history_lines,
                character_prompt=self.character_prompt,
                permanent_memory_text=memory_text,
            )
            if not reply:
                return ""

            wav = self._tts.synthesize(reply)
            async with self._playback_lock:
                voice_client = guild.voice_client
                is_playing = bool(voice_client and hasattr(voice_client, "is_playing") and voice_client.is_playing())
                if voice_client and not is_playing:
                    self._player.play_wav_bytes(guild.voice_client, wav)
            await self._history.append_line(history_channel, "Bot", reply)
            return reply
        except Exception as exc:
            self._logger.exception("Failed to process user audio: %s", exc)
            return ""

    async def process_user_text(
        self,
        *,
        guild: discord.Guild,
        history_channel: discord.TextChannel,
        user_display_name: str,
        text: str,
    ) -> str:
        cleaned = text.strip()
        if not cleaned:
            return ""
        try:
            await self._history.append_line(history_channel, user_display_name, cleaned)
            history_lines = await self._history.fetch_recent_lines(history_channel)
            memory_text = self._permanent_memory.cache.to_prompt_text()
            reply = self._gpt.generate_reply(
                user_name=user_display_name,
                transcript=cleaned,
                history_lines=history_lines,
                character_prompt=self.character_prompt,
                permanent_memory_text=memory_text,
            )
            if not reply:
                return ""
            wav = self._tts.synthesize(reply)
            async with self._playback_lock:
                voice_client = guild.voice_client
                is_playing = bool(voice_client and hasattr(voice_client, "is_playing") and voice_client.is_playing())
                if voice_client and not is_playing:
                    self._player.play_wav_bytes(guild.voice_client, wav)
            await self._history.append_line(history_channel, "Bot", reply)
            return reply
        except Exception as exc:
            self._logger.exception("Failed to process user text: %s", exc)
            return ""
