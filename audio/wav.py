from __future__ import annotations

import audioop
import io
import wave


def pcm48k_stereo_to_pcm16k_mono(pcm_bytes: bytes) -> bytes:
    if not pcm_bytes:
        return b""
    mono = audioop.tomono(pcm_bytes, 2, 0.5, 0.5)
    converted, _ = audioop.ratecv(mono, 2, 1, 48000, 16000, None)
    return converted


def pcm16k_mono_to_wav(pcm_bytes: bytes) -> bytes:
    if not pcm_bytes:
        return b""

    with io.BytesIO() as buff:
        with wave.open(buff, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(pcm_bytes)
        return buff.getvalue()


def pcm48k_stereo_to_wav16k_mono(pcm_bytes: bytes) -> bytes:
    return pcm16k_mono_to_wav(pcm48k_stereo_to_pcm16k_mono(pcm_bytes))
