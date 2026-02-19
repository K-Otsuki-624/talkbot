from __future__ import annotations

import re

from openai import OpenAI

from ai.prompt import build_system_prompt


class GPTResponder:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = OpenAI(api_key=api_key)
        self._model = model

    def generate_reply(
        self,
        user_name: str,
        transcript: str,
        history_lines: list[str],
        character_prompt: str,
        permanent_memory_text: str | None,
    ) -> str:
        system_prompt = build_system_prompt(character_prompt, permanent_memory_text, history_lines)
        message = f"{user_name}: {transcript}"

        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            temperature=0.7,
            max_tokens=200,
        )
        text = response.choices[0].message.content or ""
        return self._sanitize_reply(text.strip())

    @staticmethod
    def _sanitize_reply(text: str) -> str:
        cleaned = text.strip()
        # Remove speaker-style prefixes like "rayse: ..." or "ずんたろう：..."
        cleaned = re.sub(r"^[^:\n：]{1,40}\s*[:：]\s*", "", cleaned)
        return cleaned.strip()
