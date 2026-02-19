from audio.wav import pcm16k_mono_to_wav, pcm48k_stereo_to_pcm16k_mono


def test_pcm48_stereo_to_pcm16_mono_converts_size():
    # 48k stereo 16bit, 20ms frame => 3840 bytes
    frame = (1000).to_bytes(2, "little", signed=True) * 2
    pcm48 = frame * 960
    out = pcm48k_stereo_to_pcm16k_mono(pcm48)
    assert len(out) > 0
    # 48k -> 16k and stereo -> mono so roughly 1/6 size
    assert len(out) < len(pcm48)


def test_pcm16_to_wav_has_header():
    pcm = (1000).to_bytes(2, "little", signed=True) * 16000
    wav = pcm16k_mono_to_wav(pcm)
    assert wav[:4] == b"RIFF"
    assert b"WAVE" in wav[:16]
