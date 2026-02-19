from __future__ import annotations

import asyncio
import logging

from bot.client import create_bot
from config import Settings


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


async def amain() -> None:
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
