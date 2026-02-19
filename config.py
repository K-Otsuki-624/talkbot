from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _env_str(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Required environment variable is missing: {name}")
    return value


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


@dataclass(frozen=True)
class Settings:
    discord_token: str
    openai_api_key: str
    history_channel_id: int
    permanent_memory_channel_id: int
    voicevox_url: str
    voicevox_speaker_id: int
    history_limit: int
    vad_threshold: float
    gpt_model: str
    discord_guild_id: int

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            discord_token=_env_str("DISCORD_TOKEN", "dummy-token"),
            openai_api_key=_env_str("OPENAI_API_KEY", "dummy-openai-key"),
            history_channel_id=_env_int("HISTORY_CHANNEL_ID", 0),
            permanent_memory_channel_id=_env_int("PERMANENT_MEMORY_CHANNEL_ID", 0),
            voicevox_url=_env_str("VOICEVOX_URL", "http://localhost:50021"),
            voicevox_speaker_id=_env_int("VOICEVOX_SPEAKER_ID", 3),
            history_limit=_env_int("HISTORY_LIMIT", 50),
            vad_threshold=_env_float("VAD_THRESHOLD", 0.5),
            gpt_model=_env_str("GPT_MODEL", "gpt-4o-mini"),
            discord_guild_id=_env_int("DISCORD_GUILD_ID", 0),
        )

    def validation_errors(self) -> list[str]:
        errors: list[str] = []
        if not self.discord_token or self.discord_token == "dummy-token":
            errors.append("DISCORD_TOKEN が未設定です。")
        if not self.openai_api_key or self.openai_api_key == "dummy-openai-key":
            errors.append("OPENAI_API_KEY が未設定です。")
        if self.history_channel_id <= 0:
            errors.append("HISTORY_CHANNEL_ID は正の整数で設定してください。")
        if self.permanent_memory_channel_id <= 0:
            errors.append("PERMANENT_MEMORY_CHANNEL_ID は正の整数で設定してください。")
        if not self.voicevox_url.startswith(("http://", "https://")):
            errors.append("VOICEVOX_URL は http(s):// から始まる必要があります。")
        if self.history_limit <= 0:
            errors.append("HISTORY_LIMIT は正の整数で設定してください。")
        if not (0.0 <= self.vad_threshold <= 1.0):
            errors.append("VAD_THRESHOLD は 0.0〜1.0 の範囲で設定してください。")
        return errors
