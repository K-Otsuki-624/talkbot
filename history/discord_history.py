from __future__ import annotations

from datetime import datetime

import discord


class DiscordHistoryStore:
    def __init__(self, limit: int) -> None:
        self._limit = limit

    async def fetch_recent_lines(self, channel: discord.TextChannel) -> list[str]:
        rows: list[str] = []
        async for message in channel.history(limit=self._limit):
            content = message.content.strip()
            if not content:
                continue
            ts = message.created_at.strftime("%Y-%m-%d %H:%M:%S")
            rows.append(f"[{ts}] {message.author.display_name}: {content}")
        rows.reverse()
        return rows

    async def append_line(self, channel: discord.TextChannel, speaker: str, text: str) -> None:
        if not text.strip():
            return
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        await channel.send(f"[{now}] {speaker}: {text.strip()}")
