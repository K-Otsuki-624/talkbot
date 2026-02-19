from __future__ import annotations

from typing import Iterable


def build_permanent_memory_block(memory_text: str | None) -> str:
    if not memory_text:
        return ""
    return f"## 永続記憶（絶対に忘れないこと）\n{memory_text.strip()}\n"


def build_history_block(history_lines: Iterable[str]) -> str:
    rows = [line.strip() for line in history_lines if line.strip()]
    if not rows:
        return "## 会話履歴\n（履歴なし）"
    return "## 会話履歴\n" + "\n".join(f"- {row}" for row in rows)


def build_system_prompt(character_prompt: str, memory_text: str | None, history_lines: Iterable[str]) -> str:
    permanent_memory = build_permanent_memory_block(memory_text)
    return (
        f"{permanent_memory}\n"
        "## キャラクター設定\n"
        f"{character_prompt.strip()}\n\n"
        "## 応答ルール\n"
        "- Discord VCで会話しているため、簡潔かつ自然に返答する\n"
        "- 不明点は断定せず確認する\n"
        "- 日本語で返答する\n\n"
        "- 返答の先頭に「名前:」の形式を付けない\n\n"
        f"{build_history_block(history_lines)}"
    ).strip()
