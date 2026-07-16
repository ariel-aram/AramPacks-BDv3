from __future__ import annotations

import asyncio
import logging
import random
from collections import deque, namedtuple
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, cast

import discord
from ballsdex.packages.countryballs.countryball import BallSpawnView
from bd_models.models import Special, balls, specials
from discord import app_commands
from discord.ext import commands
from django.utils import timezone
from settings.models import settings

from specialspawn.models import SpecialSpawnConfig

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

log = logging.getLogger("specialspawn")

SPECIAL_RARITY_BOOST = 3.0
RARITY_FLATTEN_EXPONENT = 0.5

CachedMessage = namedtuple("CachedMessage", ["content", "author_id"])


@dataclass
class SpecialSpawnCooldown:
    time: datetime
    scaled_message_count: float = field(default_factory=lambda: settings.spawn_chance_min // 2)
    threshold: int = field(
        default_factory=lambda: random.randint(
            max(1, settings.spawn_chance_min // 2),
            max(2, settings.spawn_chance_max // 2),
        )
    )
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, init=False)
    message_cache: deque[CachedMessage] = field(default_factory=lambda: deque(maxlen=100))

    def reset(self, time: datetime):
        self.scaled_message_count = 1.0
        self.threshold = random.randint(
            max(1, settings.spawn_chance_min // 2),
            max(2, settings.spawn_chance_max // 2),
        )
        try:
            self.lock.release()
        except RuntimeError:
            pass
        self.time = time

    async def increase(self, message: discord.Message) -> bool:
        self.message_cache.append(CachedMessage(content=message.content, author_id=message.author.id))
        if self.lock.locked():
            return False
        async with self.lock:
            guild = message.guild
            assert guild is not None
            member_count = guild.member_count or 0
            message_multiplier = 1.0
            if member_count < 5 or member_count > 1000:
                message_multiplier /= 2
            if message._state.intents.message_content and len(message.content) < 5:
                message_multiplier /= 2
            if len(set(x.author_id for x in self.message_cache)) < 4 or (
                len(list(filter(lambda x: x.author_id == message.author.id, self.message_cache))) / 100 > 0.4
            ):
                message_multiplier /= 2
            self.scaled_message_count += message_multiplier
            await asyncio.sleep(10)
        return True

    async def check_and_increment(self, message: discord.Message) -> bool:
        guild = message.guild
        assert guild is not None
        member_count = guild.member_count or 0
        if not member_count:
            return False

        delta_t = (message.created_at - self.time).total_seconds()

        if member_count < 5:
            time_multiplier = 0.1
        elif member_count < 100:
            time_multiplier = 0.8
        elif member_count < 1000:
            time_multiplier = 0.5
        else:
            time_multiplier = 0.2

        if not await self.increase(message):
            return False

        if self.scaled_message_count + time_multiplier * (delta_t // 60) <= self.threshold:
            return False

        if delta_t < 600:
            return False

        self.reset(message.created_at)
        return True


class SpecialBallSpawnView(BallSpawnView):
    @classmethod
    async def get_random(cls, bot: "BallsDexBot"):
        countryballs = list(filter(lambda m: m.enabled, balls.values()))
        if not countryballs:
            raise RuntimeError("No ball to spawn")
        rarities = [max(x.rarity, 0.01) ** RARITY_FLATTEN_EXPONENT for x in countryballs]
        cb = random.choices(population=countryballs, weights=rarities, k=1)[0]
        return cls(bot, cb)

    def get_random_special(self) -> Special | None:  # type: ignore[override]
        population = [
            x
            for x in specials.values()
            if (x.start_date or datetime.min.replace(tzinfo=timezone.get_current_timezone()))
            <= timezone.now()
            <= (x.end_date or datetime.max.replace(tzinfo=timezone.get_current_timezone()))
        ]
        if not population:
            return None

        boosted_rarities = [x.rarity * SPECIAL_RARITY_BOOST for x in population]
        common_weight = max(0.0, 1.0 - sum(boosted_rarities))
        weights = boosted_rarities + [common_weight]
        special: Special | None = random.choices(population=population + [None], weights=weights, k=1)[0]
        return special


async def _config_special_callback(interaction: discord.Interaction, channel: discord.TextChannel):
    from discord.ext import commands as cmd

    bot = interaction.client
    if not isinstance(bot, cmd.Bot):
        return
    cog = bot.get_cog("SpecialSpawnCog")
    if cog is None:
        await interaction.response.send_message("The special spawn system is not loaded.", ephemeral=True)
        return
    await cast(SpecialSpawnCog, cog)._handle_special_config(interaction, channel)


def _try_add_config_command(bot: "BallsDexBot", cog: SpecialSpawnCog) -> bool:
    config_cog = bot.get_cog("Config")
    if config_cog is None:
        return False

    group = getattr(config_cog, "__discord_app_commands_group__", None)
    if group is None:
        return False

    special_cmd = app_commands.Command(
        name="special",
        callback=_config_special_callback,
        description="Configure the secondary special spawn channel with boosted rare rates.",
    )
    special_cmd.checks.append(app_commands.checks.has_permissions(manage_guild=True).callback)  # type: ignore[attr-defined]
    special_cmd.guild_only = True
    group.add_command(special_cmd)
    return True


class SpecialSpawnCog(commands.Cog):
    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot
        self.cache: dict[int, int] = {}
        self.cooldowns: dict[int, SpecialSpawnCooldown] = {}

    async def load_cache(self):
        i = 0
        async for config in SpecialSpawnConfig.objects.filter(special_channel__isnull=False).only(
            "guild_id", "special_channel"
        ):
            self.cache[config.guild_id] = cast(int, config.special_channel)
            i += 1
        log.info(f"Loaded {i} special spawn channel{'s' if i != 1 else ''} in cache.")

    async def _handle_special_config(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        guild = interaction.guild
        if guild is None:
            return

        config, _ = await SpecialSpawnConfig.objects.aget_or_create(guild_id=guild.id)
        config.special_channel = channel.id
        await config.asave()
        self.cache[guild.id] = channel.id

        await interaction.response.send_message(
            f"Special spawn channel set to {channel.mention}.\n"
            f"Rare {settings.plural_collectible_name} and special cards will appear "
            f"more frequently here!",
        )

    @app_commands.command()
    @app_commands.checks.has_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def specialspawn(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):
        """Configure the secondary special spawn channel with boosted rare rates."""
        await self._handle_special_config(interaction, channel)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.webhook_id is not None:
            return
        guild = message.guild
        if not guild:
            return
        if guild.id not in self.cache:
            return
        if message.channel.id != self.cache[guild.id]:
            return
        if guild.id in self.bot.blacklist_guild:
            return

        cooldown = self.cooldowns.get(guild.id)
        if not cooldown:
            cooldown = SpecialSpawnCooldown(message.created_at)
            self.cooldowns[guild.id] = cooldown

        if not await cooldown.check_and_increment(message):
            return

        channel = guild.get_channel(self.cache[guild.id])
        if not channel:
            log.warning(f"Lost special channel {self.cache[guild.id]} for guild {guild.name}.")
            del self.cache[guild.id]
            return

        ball = await SpecialBallSpawnView.get_random(self.bot)
        ball.algo = "specialspawn"
        await ball.spawn(cast(discord.TextChannel, channel))
