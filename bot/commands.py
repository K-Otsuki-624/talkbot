from __future__ import annotations

import json

import discord
from discord import app_commands
from discord.ext import commands

from bot.voice_handler import VoiceHandler
from history.discord_history import DiscordHistoryStore
from history.permanent_memory import PermanentMemoryStore


class ControlCommands(commands.Cog):
    remember = app_commands.Group(name="remember", description="永続記憶を更新する")
    memory = app_commands.Group(name="memory", description="永続記憶を表示する")
    history = app_commands.Group(name="history", description="会話履歴を管理する")

    def __init__(
        self,
        bot: commands.Bot,
        voice_handler: VoiceHandler,
        history_store: DiscordHistoryStore,
        permanent_memory_store: PermanentMemoryStore,
        history_channel_id: int,
        permanent_memory_channel_id: int,
    ) -> None:
        self.bot = bot
        self.voice_handler = voice_handler
        self.history_store = history_store
        self.permanent_memory_store = permanent_memory_store
        self.history_channel_id = history_channel_id
        self.permanent_memory_channel_id = permanent_memory_channel_id

    async def _history_channel(self, guild: discord.Guild | None) -> discord.TextChannel | None:
        if guild is None:
            return None
        channel = guild.get_channel(self.history_channel_id)
        if isinstance(channel, discord.TextChannel):
            return channel
        return None

    async def _memory_channel(self, guild: discord.Guild | None) -> discord.TextChannel | None:
        if guild is None:
            return None
        channel = guild.get_channel(self.permanent_memory_channel_id)
        if isinstance(channel, discord.TextChannel):
            return channel
        return None

    @app_commands.command(name="join", description="BotをVCに参加させる")
    async def join(self, interaction: discord.Interaction) -> None:
        history_channel = await self._history_channel(interaction.guild)
        message = await self.voice_handler.join(interaction, history_channel=history_channel)
        await interaction.response.send_message(message, ephemeral=True)

    @app_commands.command(name="leave", description="BotをVCから退出させる")
    async def leave(self, interaction: discord.Interaction) -> None:
        message = await self.voice_handler.leave(interaction)
        await interaction.response.send_message(message, ephemeral=True)

    @app_commands.command(name="status", description="Botの状態を表示する")
    async def status(self, interaction: discord.Interaction) -> None:
        if interaction.guild and interaction.guild.voice_client:
            vc_text = "VC接続中"
        else:
            vc_text = "VC未接続"
        text = (
            f"{vc_text}\n"
            f"HISTORY_CHANNEL_ID={self.history_channel_id}\n"
            f"PERMANENT_MEMORY_CHANNEL_ID={self.permanent_memory_channel_id}"
        )
        await interaction.response.send_message(text, ephemeral=True)

    @app_commands.command(name="setup_check", description="設定状態と権限を確認する")
    async def setup_check(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        if guild is None:
            await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return
        me = guild.me
        if me is None:
            await interaction.response.send_message("Bot情報の取得に失敗しました。再実行してください。", ephemeral=True)
            return

        lines: list[str] = []
        history_channel = await self._history_channel(guild)
        memory_channel = await self._memory_channel(guild)

        if history_channel is None:
            lines.append("NG: HISTORY_CHANNEL_ID のチャンネルが見つかりません。")
        else:
            perms = history_channel.permissions_for(me)
            if perms.send_messages and perms.read_message_history:
                lines.append("OK: 履歴チャンネルの参照/投稿権限があります。")
            else:
                lines.append("NG: 履歴チャンネルの権限が不足しています。")

        if memory_channel is None:
            lines.append("NG: PERMANENT_MEMORY_CHANNEL_ID のチャンネルが見つかりません。")
        else:
            perms = memory_channel.permissions_for(me)
            if perms.send_messages and perms.read_message_history:
                lines.append("OK: 永続記憶チャンネルの参照/投稿権限があります。")
            else:
                lines.append("NG: 永続記憶チャンネルの権限が不足しています。")

        if guild.voice_client:
            lines.append("INFO: VC接続中です。")
        else:
            lines.append("INFO: VC未接続です（/join で接続）。")

        await interaction.response.send_message("\n".join(lines), ephemeral=True)

    @app_commands.command(name="character", description="キャラクター設定を変更する")
    @app_commands.describe(name="キャラクター設定テキスト")
    async def character(self, interaction: discord.Interaction, name: str) -> None:
        self.voice_handler.character_prompt = name.strip()
        await interaction.response.send_message("キャラクター設定を更新しました。", ephemeral=True)

    @app_commands.command(name="talk", description="テキスト入力で応答パイプラインを確認する")
    @app_commands.describe(text="Botに話しかけるテキスト")
    async def talk(self, interaction: discord.Interaction, text: str) -> None:
        if interaction.guild is None:
            await interaction.response.send_message("サーバー内で実行してください。", ephemeral=True)
            return
        history_channel = await self._history_channel(interaction.guild)
        if history_channel is None:
            await interaction.response.send_message("履歴チャンネルが見つかりません。", ephemeral=True)
            return
        user_name = interaction.user.display_name if isinstance(interaction.user, discord.Member) else "User"
        await interaction.response.defer(ephemeral=True, thinking=True)
        reply = await self.voice_handler.process_user_text(
            guild=interaction.guild,
            history_channel=history_channel,
            user_display_name=user_name,
            text=text,
        )
        if not reply:
            await interaction.followup.send("応答生成に失敗しました。設定を確認してください。", ephemeral=True)
            return
        await interaction.followup.send(f"応答: {reply}", ephemeral=True)

    @history.command(name="clear", description="会話履歴をクリアする")
    async def history_clear(self, interaction: discord.Interaction) -> None:
        channel = await self._history_channel(interaction.guild)
        if channel is None:
            await interaction.response.send_message("履歴チャンネルが見つかりません。", ephemeral=True)
            return
        deleted = 0
        async for message in channel.history(limit=200):
            await message.delete()
            deleted += 1
        await interaction.response.send_message(f"履歴を{deleted}件削除しました。", ephemeral=True)

    @remember.command(name="name", description="Botの名前を記憶させる")
    @app_commands.describe(name="Bot名")
    async def remember_name(self, interaction: discord.Interaction, name: str) -> None:
        channel = await self._memory_channel(interaction.guild)
        if channel is None:
            await interaction.response.send_message("永続記憶チャンネルが見つかりません。", ephemeral=True)
            return
        await self.permanent_memory_store.remember_name(channel, name)
        await interaction.response.send_message("Bot名を更新しました。", ephemeral=True)

    @remember.command(name="member", description="メンバーの読み方を記憶させる")
    @app_commands.describe(member="対象メンバー", reading="読み方")
    async def remember_member(self, interaction: discord.Interaction, member: discord.Member, reading: str) -> None:
        channel = await self._memory_channel(interaction.guild)
        if channel is None:
            await interaction.response.send_message("永続記憶チャンネルが見つかりません。", ephemeral=True)
            return
        await self.permanent_memory_store.remember_member(channel, member.id, member.display_name, reading)
        await interaction.response.send_message("メンバー情報を更新しました。", ephemeral=True)

    @remember.command(name="note", description="自由メモを記憶させる")
    @app_commands.describe(note="メモ内容")
    async def remember_note(self, interaction: discord.Interaction, note: str) -> None:
        channel = await self._memory_channel(interaction.guild)
        if channel is None:
            await interaction.response.send_message("永続記憶チャンネルが見つかりません。", ephemeral=True)
            return
        await self.permanent_memory_store.remember_note(channel, note)
        await interaction.response.send_message("メモを追加しました。", ephemeral=True)

    @memory.command(name="show", description="永続記憶を表示する")
    async def memory_show(self, interaction: discord.Interaction) -> None:
        payload = json.dumps(self.permanent_memory_store.cache.to_dict(), ensure_ascii=False, indent=2)
        await interaction.response.send_message(
            f"```json\n{payload}\n```",
            ephemeral=True,
        )
