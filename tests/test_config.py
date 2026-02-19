from config import Settings


def test_settings_defaults(monkeypatch):
    for key in [
        "DISCORD_TOKEN",
        "OPENAI_API_KEY",
        "HISTORY_CHANNEL_ID",
        "PERMANENT_MEMORY_CHANNEL_ID",
        "VOICEVOX_URL",
        "VOICEVOX_SPEAKER_ID",
        "HISTORY_LIMIT",
        "VAD_THRESHOLD",
        "GPT_MODEL",
    ]:
        monkeypatch.delenv(key, raising=False)

    settings = Settings.from_env()
    assert settings.voicevox_url == "http://localhost:50021"
    assert settings.voicevox_speaker_id == 3
    assert settings.history_limit == 50
    assert settings.vad_threshold == 0.5
    assert settings.gpt_model == "gpt-4o-mini"


def test_settings_override(monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "abc")
    monkeypatch.setenv("OPENAI_API_KEY", "xyz")
    monkeypatch.setenv("HISTORY_CHANNEL_ID", "123")
    monkeypatch.setenv("PERMANENT_MEMORY_CHANNEL_ID", "456")
    monkeypatch.setenv("VOICEVOX_URL", "http://voicevox:50021")
    monkeypatch.setenv("VOICEVOX_SPEAKER_ID", "8")
    monkeypatch.setenv("HISTORY_LIMIT", "25")
    monkeypatch.setenv("VAD_THRESHOLD", "0.8")
    monkeypatch.setenv("GPT_MODEL", "gpt-4o-mini")

    settings = Settings.from_env()
    assert settings.discord_token == "abc"
    assert settings.openai_api_key == "xyz"
    assert settings.history_channel_id == 123
    assert settings.permanent_memory_channel_id == 456
    assert settings.voicevox_url == "http://voicevox:50021"
    assert settings.voicevox_speaker_id == 8
    assert settings.history_limit == 25
    assert settings.vad_threshold == 0.8
    assert settings.validation_errors() == []


def test_settings_validation_detects_dummy(monkeypatch):
    monkeypatch.setenv("DISCORD_TOKEN", "dummy-token")
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-openai-key")
    monkeypatch.setenv("HISTORY_CHANNEL_ID", "0")
    monkeypatch.setenv("PERMANENT_MEMORY_CHANNEL_ID", "0")

    settings = Settings.from_env()
    errors = settings.validation_errors()
    assert any("DISCORD_TOKEN" in e for e in errors)
    assert any("OPENAI_API_KEY" in e for e in errors)
