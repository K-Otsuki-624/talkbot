from __future__ import annotations

from io import BytesIO

from openai import OpenAI


class WhisperTranscriber:
    def __init__(self, api_key: str) -> None:
        self._client = OpenAI(api_key=api_key)

    def transcribe_ja(self, wav_bytes: bytes) -> str:
        if not wav_bytes:
            return ""
        file_like = BytesIO(wav_bytes)
        file_like.name = "audio.wav"
        result = self._client.audio.transcriptions.create(
            model="whisper-1",
            file=file_like,
            language="ja",
            timeout=10,
        )
        return (result.text or "").strip()
