from __future__ import annotations

import asyncio
import logging

import discord

from bot.client import create_bot
from config import Settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def _load_opus_if_needed() -> None:
    if discord.opus.is_loaded():
        return
    candidates = [
        "libopus.so.0",
        "libopus.so",
        "opus",
        "opus.dll",
        "libopus-0.dll",
    ]
    for path in candidates:
        try:
            discord.opus.load_opus(path)
            logger.info("Opus library loaded: %s", path)
            return
        except OSError:
            continue
    logger.warning("Opus library is not loaded. VC receive/transcribe will not work.")


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
