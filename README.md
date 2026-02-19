# Discord AI Voice Bot

設計書 `discord bot design v2.docx` に沿って、Phase 1〜7 相当のコード基盤を実装済みです。  
残作業は主に外部サービス側の設定です。

## 実装済み機能

- `/join`, `/leave`, `/status`, `/setup_check`
- `/character`
- `/history clear`
- `/remember name`, `/remember member`, `/remember note`
- `/memory show`
- `/talk`（テキスト入力で GPT + VOICEVOX パイプライン確認）
- VC音声のリアルタイム受信（`discord-ext-voice-recv` ベース）
- 会話履歴チャンネル管理
- 永続記憶チャンネル管理（JSON）

## ローカル起動

1. Python 3.11+ を準備
2. 依存関係をインストール
   - `pip install -r requirements.txt`
3. `.env.example` を `.env` にコピーして設定
4. 起動
   - `python main.py`

## 必須の外部設定（ここだけ実施すれば起動可能）

### 1) Discord Developer Portal

- Bot作成してトークンを取得 (`DISCORD_TOKEN`)
- Privileged Gateway Intents を有効化
  - Message Content Intent
  - Server Members Intent（必要に応じて）
- Botを対象サーバーへ招待
- 付与権限の例
  - Send Messages
  - Read Message History
  - Connect / Speak（VC）
  - Use Slash Commands

### 2) Discord サーバー側

- 会話履歴チャンネルを作成（例: `#bot-memory`）  
  `HISTORY_CHANNEL_ID` に設定
- 永続記憶チャンネルを作成（例: `#bot-permanent-memory`）  
  `PERMANENT_MEMORY_CHANNEL_ID` に設定
- テスト用サーバーIDを `DISCORD_GUILD_ID` に設定すると、Slashコマンド反映が速い

### 3) OpenAI

- APIキー作成 (`OPENAI_API_KEY`)
- Whisper / GPT-4o-mini が利用可能な課金状態を確認

### 4) VOICEVOX

- ローカル利用: `VOICEVOX_URL=http://localhost:50021`
- Railway等で別サービス化した場合はそのURLを設定

### 5) Railway（任意・本番）

- 推奨は2サービス構成
  - `discord-bot`: このリポジトリを通常デプロイ（Nixpacks）
  - `voicevox`: 同じリポジトリをDockerデプロイし、Dockerfileパスを `voicevox/Dockerfile` に指定
- BotをDocker運用したい場合は `Dockerfile.bot` を使用
- VC音声受信には `libopus` が必要（`nixpacks.toml` / `Dockerfile.bot` で導入済み）
- `discord-bot` の環境変数に `.env` の値を設定
- `VOICEVOX_URL` には `voicevox` サービスのURLを設定

## 起動後の確認手順

1. `/setup_check` でチャンネル参照/投稿権限を確認
2. `/join` でVC接続
3. `/talk こんにちは` で GPT + VOICEVOX 応答確認
4. `/remember name ずんたろう` などで永続記憶を更新
5. `/memory show` で反映確認
6. 必要に応じて外部接続チェック
   - `python scripts/preflight_check.py`

## テスト

- `pytest -q`
