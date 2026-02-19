from __future__ import annotations

import logging

import discord
from discord.errors import Forbidden, HTTPException
from discord.ext import commands

from ai.gpt import GPTResponder
from audio.player import VoicePlayer
from audio.tts import VoiceVoxTTS
from audio.vad import VADSegmenter
from audio.whisper import WhisperTranscriber
from bot.commands import ControlCommands
from bot.voice_handler import VoiceHandler
from config import Settings
from history.discord_history import DiscordHistoryStore
from history.permanent_memory import PermanentMemoryStore

logger = logging.getLogger(__name__)


class DiscordAIBot(commands.Bot):
    def __init__(self, settings: Settings) -> None:
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.guilds = True

        super().__init__(command_prefix="!", intents=intents)
        self.settings = settings

        history_store = DiscordHistoryStore(limit=settings.history_limit)
        permanent_memory_store = PermanentMemoryStore()
        voice_handler = VoiceHandler(
            vad=VADSegmenter(settings.vad_threshold),
            whisper=WhisperTranscriber(settings.openai_api_key),
            gpt=GPTResponder(settings.openai_api_key, settings.gpt_model),
            tts=VoiceVoxTTS(settings.voicevox_url, settings.voicevox_speaker_id),
            player=VoicePlayer(),
            history=history_store,
            permanent_memory=permanent_memory_store,
        )
        self.voice_handler = voice_handler
        self.history_store = history_store
        self.permanent_memory_store = permanent_memory_store

    async def setup_hook(self) -> None:
        await self.add_cog(
            ControlCommands(
                self,
                self.voice_handler,
                self.history_store,
                self.permanent_memory_store,
                self.settings.history_channel_id,
                self.settings.permanent_memory_channel_id,
            )
        )
        # Always sync global commands first so misconfigured guild IDs do not hide commands completely.
        global_synced = await self.tree.sync()
        logger.info("Application commands synced globally (count=%s).", len(global_synced))

        if self.settings.discord_guild_id > 0:
            guild_obj = discord.Object(id=self.settings.discord_guild_id)
            try:
                # Copy global commands to target guild for immediate availability.
                self.tree.copy_global_to(guild=guild_obj)
                guild_synced = await self.tree.sync(guild=guild_obj)
                logger.info(
                    "Application commands synced to guild: %s (count=%s)",
                    self.settings.discord_guild_id,
                    len(guild_synced),
                )
            except (Forbidden, HTTPException) as exc:
                logger.warning(
                    "Guild command sync failed for guild=%s: %s. Global sync is still available.",
                    self.settings.discord_guild_id,
                    exc,
                )

    async def on_ready(self) -> None:
        logger.info("Logged in as %s", self.user)
        if self.settings.discord_guild_id > 0:
            target = self.get_guild(self.settings.discord_guild_id)
            if target is None:
                logger.warning(
                    "DISCORD_GUILD_ID=%s is not found. Check bot invite target guild.",
                    self.settings.discord_guild_id,
                )
        # 起動時に永続記憶をロード
        if self.settings.permanent_memory_channel_id:
            for guild in self.guilds:
                channel = guild.get_channel(self.settings.permanent_memory_channel_id)
                if isinstance(channel, discord.TextChannel):
                    try:
                        await self.permanent_memory_store.load_from_channel(channel)
                        logger.info("Permanent memory loaded from channel: %s", channel.id)
                    except (Forbidden, HTTPException) as exc:
                        logger.warning(
                            "Permanent memory load skipped due to channel access/API issue: %s (channel=%s)",
                            exc,
                            channel.id,
                        )
                    break

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return
        await self.process_commands(message)


def create_bot(settings: Settings) -> DiscordAIBot:
    return DiscordAIBot(settings)
