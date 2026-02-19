import types
from unittest.mock import Mock

import pytest

from bot.voice_handler import VoiceHandler


class DummyHistory:
    def __init__(self):
        self.rows = []

    async def append_line(self, channel, speaker, text):
        self.rows.append((speaker, text))

    async def fetch_recent_lines(self, channel):
        return [f"{s}: {t}" for s, t in self.rows]


class DummyMemoryStore:
    def __init__(self):
        self.cache = types.SimpleNamespace(to_prompt_text=lambda: "memory")


@pytest.mark.asyncio
async def test_process_user_audio_pipeline_runs():
    vad = Mock(has_speech=Mock(return_value=True))
    whisper = Mock(transcribe_ja=Mock(return_value="こんにちは"))
    gpt = Mock(generate_reply=Mock(return_value="やっほー"))
    tts = Mock(synthesize=Mock(return_value=b"wav"))
    player = Mock(play_wav_bytes=Mock())
    history = DummyHistory()
    memory = DummyMemoryStore()

    handler = VoiceHandler(vad, whisper, gpt, tts, player, history, memory)
    guild = types.SimpleNamespace(voice_client=object())
    channel = object()

    reply = await handler.process_user_audio(
        guild=guild,
        history_channel=channel,
        user_display_name="alice",
        pcm16_mono=b"1234",
        wav_bytes=b"5678",
    )

    assert reply == "やっほー"
    player.play_wav_bytes.assert_called_once()
    assert history.rows[0] == ("alice", "こんにちは")
    assert history.rows[-1] == ("Bot", "やっほー")


@pytest.mark.asyncio
async def test_process_user_audio_skips_when_vad_false():
    vad = Mock(has_speech=Mock(return_value=False))
    whisper = Mock(transcribe_ja=Mock())
    gpt = Mock(generate_reply=Mock())
    tts = Mock(synthesize=Mock())
    player = Mock(play_wav_bytes=Mock())
    history = DummyHistory()
    memory = DummyMemoryStore()

    handler = VoiceHandler(vad, whisper, gpt, tts, player, history, memory)
    guild = types.SimpleNamespace(voice_client=object())
    channel = object()

    reply = await handler.process_user_audio(
        guild=guild,
        history_channel=channel,
        user_display_name="alice",
        pcm16_mono=b"",
        wav_bytes=b"",
    )
    assert reply == ""
    whisper.transcribe_ja.assert_not_called()


@pytest.mark.asyncio
async def test_process_user_text_pipeline_runs():
    vad = Mock(has_speech=Mock(return_value=True))
    whisper = Mock(transcribe_ja=Mock(return_value="こんにちは"))
    gpt = Mock(generate_reply=Mock(return_value="了解です"))
    tts = Mock(synthesize=Mock(return_value=b"wav"))
    player = Mock(play_wav_bytes=Mock())
    history = DummyHistory()
    memory = DummyMemoryStore()

    handler = VoiceHandler(vad, whisper, gpt, tts, player, history, memory)
    guild = types.SimpleNamespace(voice_client=types.SimpleNamespace(is_playing=lambda: False))
    channel = object()

    reply = await handler.process_user_text(
        guild=guild,
        history_channel=channel,
        user_display_name="alice",
        text="テストです",
    )

    assert reply == "了解です"
    player.play_wav_bytes.assert_called_once()
