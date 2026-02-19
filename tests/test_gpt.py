from ai.gpt import GPTResponder


def test_sanitize_reply_removes_name_prefix_ascii_colon():
    text = "rayse: 了解、今から入るね。"
    assert GPTResponder._sanitize_reply(text) == "了解、今から入るね。"


def test_sanitize_reply_removes_name_prefix_japanese_colon():
    text = "ずんたろう：うん、いいよ。"
    assert GPTResponder._sanitize_reply(text) == "うん、いいよ。"


def test_sanitize_reply_keeps_normal_sentence():
    text = "今いくよ。ちょっと待ってね。"
    assert GPTResponder._sanitize_reply(text) == text
