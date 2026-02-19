from history.permanent_memory import PermanentMemory


def test_permanent_memory_prompt_text():
    memory = PermanentMemory(
        bot_name="ずんたろう",
        bot_personality="フレンドリー",
        members={"1": {"display_name": "kazuya", "reading": "かずや"}},
        notes=["ゲームの話が好き"],
    )
    text = memory.to_prompt_text()
    assert "ずんたろう" in text
    assert "kazuya" in text
    assert "ゲームの話が好き" in text


def test_permanent_memory_round_trip():
    original = PermanentMemory(
        bot_name="bot",
        bot_personality="kind",
        members={"1": {"display_name": "a", "reading": "えー"}},
        notes=["n1"],
    )
    restored = PermanentMemory.from_dict(original.to_dict())
    assert restored.to_dict() == original.to_dict()
