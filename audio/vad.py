from __future__ import annotations

import audioop


class VADSegmenter:
    """Simple RMS-based VAD for phase development/testing."""

    def __init__(self, threshold: float = 0.5) -> None:
        raw = max(0.0, min(1.0, threshold))
        # In the design doc, threshold=0.5 is for Silero probability scale.
        # Convert that value to a practical RMS amplitude threshold for PCM.
        if raw > 0.2:
            self.threshold = max(0.003, raw * 0.04)
        else:
            self.threshold = raw

    def has_speech(self, pcm16_mono: bytes) -> bool:
        if not pcm16_mono:
            return False
        rms = audioop.rms(pcm16_mono, 2)
        normalized = min(1.0, rms / 32768.0)
        return normalized >= self.threshold
