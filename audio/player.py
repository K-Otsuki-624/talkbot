from __future__ import annotations

import tempfile
from pathlib import Path

import discord


class VoicePlayer:
    """Small helper that plays WAV bytes via FFmpegPCMAudio."""

    def __init__(self) -> None:
        self._temp_files: list[Path] = []

    def play_wav_bytes(self, voice_client: discord.VoiceClient, wav_data: bytes) -> None:
        if not wav_data:
            return
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_file.write(wav_data)
        temp_file.flush()
        temp_path = Path(temp_file.name)
        temp_file.close()
        self._temp_files.append(temp_path)

        def _after_playback(_: Exception | None) -> None:
            try:
                temp_path.unlink(missing_ok=True)
            finally:
                if temp_path in self._temp_files:
                    self._temp_files.remove(temp_path)

        source = discord.FFmpegPCMAudio(str(temp_path))
        voice_client.play(source, after=_after_playback)
