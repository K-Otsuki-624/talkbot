from __future__ import annotations

import asyncio
import ctypes.util
import logging
from pathlib import Path

import discord

from bot.client import create_bot
from config import Settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _load_opus_if_needed() -> None:
    if discord.opus.is_loaded():
        return
    discovered = ctypes.util.find_library("opus")
    candidates = [
        discovered or "",
        "libopus.so.0",
        "libopus.so",
        "opus",
        "opus.dll",
        "libopus-0.dll",
        "/usr/lib/x86_64-linux-gnu/libopus.so.0",
        "/usr/lib/x86_64-linux-gnu/libopus.so",
        "/lib/x86_64-linux-gnu/libopus.so.0",
        "/lib/x86_64-linux-gnu/libopus.so",
    ]
    checked: list[str] = []
    for path in candidates:
        if not path:
            continue
        try:
            discord.opus.load_opus(path)
            logger.info("Opus library loaded: %s", path)
            return
        except OSError as exc:
            checked.append(f"{path} ({exc})")
            continue
    existing_hint = [str(p) for p in Path("/usr/lib/x86_64-linux-gnu").glob("libopus*")] if Path("/usr/lib/x86_64-linux-gnu").exists() else []
    logger.warning(
        "Opus library is not loaded. VC receive/transcribe will not work. find_library=%s checked=%s existing=%s",
        discovered,
        checked,
        existing_hint,
    )


async def amain() -> None:
    _load_opus_if_needed()
    settings = Settings.from_env()
    validation_errors = settings.validation_errors()
    if validation_errors:
        joined = "\n".join(f"- {msg}" for msg in validation_errors)
        raise RuntimeError(f".env 設定エラー:\n{joined}")
    bot = create_bot(settings)
    await bot.start(settings.discord_token)


if __name__ == "__main__":
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass
