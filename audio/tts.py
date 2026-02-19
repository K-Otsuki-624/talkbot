from __future__ import annotations

import httpx


class VoiceVoxTTS:
    def __init__(self, base_url: str, speaker_id: int) -> None:
        self._base_url = base_url.rstrip("/")
        self._speaker_id = speaker_id

    def synthesize(self, text: str) -> bytes:
        if not text.strip():
            return b""
        with httpx.Client(timeout=20.0) as client:
            query_res = client.post(
                f"{self._base_url}/audio_query",
                params={"text": text, "speaker": self._speaker_id},
            )
            query_res.raise_for_status()
            synthesis_res = client.post(
                f"{self._base_url}/synthesis",
                params={"speaker": self._speaker_id},
                json=query_res.json(),
            )
            synthesis_res.raise_for_status()
            return synthesis_res.content
