from ai.prompt import build_system_prompt


def test_build_system_prompt_contains_required_sections():
    text = build_system_prompt(
        character_prompt="フレンドリーに話す",
        memory_text="あなたの名前は「ずんたろう」です。",
        history_lines=["user1: こんにちは", "Bot: やっほー"],
    )
    assert "## 永続記憶（絶対に忘れないこと）" in text
    assert "## キャラクター設定" in text
    assert "## 会話履歴" in text
    assert "- user1: こんにちは" in text
