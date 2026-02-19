from audio.vad import VADSegmenter


def _pcm_s16le_from_constant(amplitude: int, samples: int) -> bytes:
    # 16-bit signed PCM little-endian
    value = int(amplitude).to_bytes(2, byteorder="little", signed=True)
    return value * samples


def test_vad_detects_speech():
    vad = VADSegmenter(threshold=0.05)
    loud = _pcm_s16le_from_constant(10000, 3200)
    assert vad.has_speech(loud) is True


def test_vad_detects_silence():
    vad = VADSegmenter(threshold=0.05)
    silence = _pcm_s16le_from_constant(0, 3200)
    assert vad.has_speech(silence) is False


def test_vad_threshold_compatible_with_design_value():
    # design default 0.5 (Silero scale) should still pass with normal speech level
    vad = VADSegmenter(threshold=0.5)
    normal_voice = _pcm_s16le_from_constant(2000, 3200)
    assert vad.has_speech(normal_voice) is True
