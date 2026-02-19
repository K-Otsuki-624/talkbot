from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import discord
from discord.errors import Forbidden


@dataclass
class PermanentMemory:
    bot_name: str = "AI Assistant"
    bot_personality: str = "フレンドリーに会話する"
    members: dict[str, dict[str, str]] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PermanentMemory":
        return cls(
            bot_name=str(data.get("bot_name", "AI Assistant")),
            bot_personality=str(data.get("bot_personality", "フレンドリーに会話する")),
            members=dict(data.get("members", {})),
            notes=list(data.get("notes", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "bot_name": self.bot_name,
            "bot_personality": self.bot_personality,
            "members": self.members,
            "notes": self.notes,
        }

    def to_prompt_text(self) -> str:
        lines = [f"あなたの名前は「{self.bot_name}」です。", f"性格: {self.bot_personality}"]
        if self.members:
            lines.append("メンバー情報:")
            for m in self.members.values():
                lines.append(f"- {m.get('display_name', 'unknown')} -> 読み方: {m.get('reading', '')}")
        if self.notes:
            lines.append("メモ:")
            for note in self.notes:
                lines.append(f"- {note}")
        return "\n".join(lines)


class PermanentMemoryStore:
    def __init__(self) -> None:
        self._cache = PermanentMemory()

    @property
    def cache(self) -> PermanentMemory:
        return self._cache

    async def load_from_channel(self, channel: discord.TextChannel) -> PermanentMemory:
        async for message in channel.history(limit=50):
            try:
                payload = json.loads(message.content)
                self._cache = PermanentMemory.from_dict(payload)
                return self._cache
            except (json.JSONDecodeError, TypeError, ValueError):
                continue
        # JSONが見つからない場合はデフォルトで初期化
        self._cache = PermanentMemory()
        return self._cache

    async def save_to_channel(self, channel: discord.TextChannel) -> None:
        # 最新1件のみを真実ソースとして残すため、既存投稿を削除してから再投稿する
        async for message in channel.history(limit=50):
            try:
                await message.delete()
            except Forbidden:
                # 権限不足なら削除をスキップし、追記のみ行う
                break
        await channel.send(json.dumps(self._cache.to_dict(), ensure_ascii=False))

    async def remember_name(self, channel: discord.TextChannel, name: str) -> None:
        self._cache.bot_name = name.strip() or self._cache.bot_name
        await self.save_to_channel(channel)

    async def remember_member(self, channel: discord.TextChannel, user_id: int, display_name: str, reading: str) -> None:
        self._cache.members[str(user_id)] = {"display_name": display_name, "reading": reading}
        await self.save_to_channel(channel)

    async def remember_note(self, channel: discord.TextChannel, note: str) -> None:
        cleaned = note.strip()
        if cleaned:
            self._cache.notes.append(cleaned)
            await self.save_to_channel(channel)
