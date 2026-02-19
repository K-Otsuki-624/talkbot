from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import Settings


async def check_voicevox(url: str) -> tuple[bool, str]:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{url.rstrip('/')}/version")
            if res.status_code == 200:
                return True, "VOICEVOX reachable"
            return False, f"VOICEVOX status={res.status_code}"
    except Exception as exc:
        return False, f"VOICEVOX unreachable: {exc}"


def check_openai(api_key: str) -> tuple[bool, str]:
    try:
        client = OpenAI(api_key=api_key)
        client.models.list()
        return True, "OpenAI reachable"
    except Exception as exc:
        return False, f"OpenAI unreachable: {exc}"


async def main() -> int:
    settings = Settings.from_env()
    errors = settings.validation_errors()
    if errors:
        print("NG: .env validation failed")
        for err in errors:
            print(f" - {err}")
        return 1

    ok_openai, msg_openai = check_openai(settings.openai_api_key)
    ok_voicevox, msg_voicevox = await check_voicevox(settings.voicevox_url)

    print(("OK" if ok_openai else "NG") + f": {msg_openai}")
    print(("OK" if ok_voicevox else "NG") + f": {msg_voicevox}")

    return 0 if (ok_openai and ok_voicevox) else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
