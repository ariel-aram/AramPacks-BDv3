import logging
import random
from typing import TYPE_CHECKING

import discord
from bd_models.models import Ball, BallInstance, Player, Special
from discord import app_commands
from discord.ext import commands
from django.utils import timezone

from ..models import AdventClaim, AdventDayConfig, RewardType

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

log = logging.getLogger("advent_app.advent_ext")

CALENDAR_DAYS = 25


class CalendarDayButton(discord.ui.Button["AdventCalendarView"]):
    def __init__(self, day: int, claimed: bool, configured: bool, is_today: bool):
        if claimed:
            label = f"{day}"
            style = discord.ButtonStyle.green
            emoji = "\u2705"
        elif is_today:
            label = f"{day}"
            style = discord.ButtonStyle.primary
            emoji = "\U0001f4c5"
        elif configured:
            label = f"{day}"
            style = discord.ButtonStyle.secondary
            emoji = "\U0001f381"
        else:
            label = f"{day}"
            style = discord.ButtonStyle.gray
            emoji = "\u2b1b"

        super().__init__(label=label, emoji=emoji, style=style, row=(day - 1) // 5)
        self.day = day
        self.claimed = claimed

    async def callback(self, interaction: discord.Interaction) -> None:
        view = self.view
        if view is None:
            return
        await view.show_day_detail(interaction, self.day)


class AdventCalendarView(discord.ui.View):
    def __init__(self, player_id: int):
        super().__init__(timeout=120)
        self.player_id = player_id

    async def show_day_detail(self, interaction: discord.Interaction, day: int) -> None:
        config = await AdventDayConfig.objects.filter(day=day).select_related("ball", "special").afirst()
        claimed = await AdventClaim.objects.filter(player_id=self.player_id, day=day).aexists()

        if not config:
            await interaction.response.send_message(f"Day {day} has no reward configured yet.", ephemeral=True)
            return

        reward_type_name = {
            RewardType.RANDOM_SPECIAL.value: "\U0001f3b0 Random Special",
            RewardType.SELECTED_BALL.value: "\U0001f3b1 Selected Ball",
            RewardType.SELECTED_BALL_WITH_SPECIAL.value: "\u2728 Selected Ball + Special",
        }.get(config.reward_type, "Unknown")

        embed = discord.Embed(
            title=f"\U0001f381 Advent Day {day}",
            color=discord.Color.green() if claimed else discord.Color.gold(),
        )
        embed.add_field(name="Reward Type", value=reward_type_name, inline=False)
        if config.ball:
            ball_emoji = ""
            if config.ball.emoji_id and interaction.client:
                emoji_obj = interaction.client.get_emoji(config.ball.emoji_id)
                if emoji_obj:
                    ball_emoji = f"{emoji_obj} "
            embed.add_field(name="Ball", value=f"{ball_emoji}{config.ball.country}", inline=True)
        if config.special:
            embed.add_field(name="Special", value=config.special.name, inline=True)
        if config.label:
            embed.add_field(name="Note", value=config.label, inline=False)
        embed.set_footer(text="\u2705 Claimed!" if claimed else "\u23f0 Not yet claimed — use /advent claim")

        await interaction.response.send_message(embed=embed, ephemeral=True)


class AdventCalendar(commands.Cog):
    """Advent Calendar cog for Ballsdex v3."""

    group = app_commands.Group(name="advent", description="Advent Calendar commands.")

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot

    @group.command(name="claim", description="Claim your daily advent calendar reward.")
    async def claim(self, interaction: discord.Interaction["BallsDexBot"]):
        user_id = interaction.user.id
        blacklist = getattr(self.bot, "blacklist", set())
        if user_id in blacklist:
            await interaction.response.send_message(
                "You are blacklisted and cannot claim advent rewards.", ephemeral=True
            )
            return

        now = timezone.now()
        today = now.day

        day_config = (
            await AdventDayConfig.objects.filter(day=today, enabled=True).select_related("ball", "special").afirst()
        )
        if not day_config:
            await interaction.response.send_message(
                "No advent reward is configured for today. Check back later!", ephemeral=True
            )
            return

        player, _ = await Player.objects.aget_or_create(discord_id=user_id)

        already_claimed = await AdventClaim.objects.filter(player=player, day=today).aexists()
        if already_claimed:
            await interaction.response.send_message("You have already claimed today's advent reward!", ephemeral=True)
            return

        reward_type = day_config.reward_type
        ball_obj = day_config.ball
        special_obj = day_config.special

        embed = discord.Embed(title=f"\U0001f381 Advent Calendar - Day {today}", color=discord.Color.gold())
        reward_lines = []

        if reward_type == RewardType.RANDOM_SPECIAL.value:
            enabled_balls = [b async for b in Ball.enabled_objects.all()]
            all_specials = [s async for s in Special.objects.all()]
            if enabled_balls and all_specials:
                chosen_ball = random.choice(enabled_balls)
                chosen_special = random.choice(all_specials)
                await BallInstance.objects.acreate(
                    ball=chosen_ball,
                    player=player,
                    special=chosen_special,
                )
                emoji = ""
                if chosen_ball.emoji_id and interaction.client:
                    emoji_obj = interaction.client.get_emoji(chosen_ball.emoji_id)
                    if emoji_obj:
                        emoji = f"{emoji_obj} "
                reward_lines.append(f"{emoji}{chosen_ball.country} + **{chosen_special.name}**")
            else:
                reward_lines.append("\u26a0\ufe0f No balls or specials available. Contact an admin.")

        elif reward_type == RewardType.SELECTED_BALL.value:
            if ball_obj:
                await BallInstance.objects.acreate(
                    ball=ball_obj,
                    player=player,
                )
                emoji = ""
                if ball_obj.emoji_id and interaction.client:
                    emoji_obj = interaction.client.get_emoji(ball_obj.emoji_id)
                    if emoji_obj:
                        emoji = f"{emoji_obj} "
                reward_lines.append(f"{emoji}{ball_obj.country}")
            else:
                reward_lines.append("\u26a0\ufe0f No ball configured for today. Contact an admin.")

        elif reward_type == RewardType.SELECTED_BALL_WITH_SPECIAL.value:
            if ball_obj:
                await BallInstance.objects.acreate(
                    ball=ball_obj,
                    player=player,
                    special=special_obj,
                )
                emoji = ""
                if ball_obj.emoji_id and interaction.client:
                    emoji_obj = interaction.client.get_emoji(ball_obj.emoji_id)
                    if emoji_obj:
                        emoji = f"{emoji_obj} "
                special_name = special_obj.name if special_obj else "None"
                reward_lines.append(f"{emoji}{ball_obj.country} with **{special_name}**")
            else:
                reward_lines.append("\u26a0\ufe0f No ball configured for today. Contact an admin.")

        await AdventClaim.objects.acreate(player=player, day=today)

        if reward_lines:
            embed.add_field(name="\U0001f4e6 Reward", value="\n".join(reward_lines), inline=False)
        embed.add_field(name="\U0001f464 Claimed by", value=interaction.user.mention, inline=False)

        if day_config.label:
            embed.set_footer(text=day_config.label)

        await interaction.response.send_message(embed=embed)

    @group.command(name="calendar", description="View your advent calendar progress.")
    async def calendar(self, interaction: discord.Interaction["BallsDexBot"]):
        user_id = interaction.user.id
        blacklist = getattr(self.bot, "blacklist", set())
        if user_id in blacklist:
            await interaction.response.send_message("You are blacklisted.", ephemeral=True)
            return

        player = await Player.objects.filter(discord_id=user_id).afirst()

        claimed_set: set[int] = set()
        if player:
            async for claim in AdventClaim.objects.filter(player=player).order_by("day"):
                claimed_set.add(claim.day)

        all_configs = {c.day: c async for c in AdventDayConfig.objects.filter(enabled=True)}

        now = timezone.now()
        today = now.day

        view = AdventCalendarView(player_id=user_id if player else 0)

        for day in range(1, CALENDAR_DAYS + 1):
            claimed = day in claimed_set
            configured = day in all_configs
            is_today = day == today
            view.add_item(CalendarDayButton(day, claimed, configured, is_today))

        claimed_count = len(claimed_set)
        embed = discord.Embed(
            title=f"\U0001f4c5 Advent Calendar — {interaction.user.display_name}",
            description=(
                f"**{claimed_count} / {len(all_configs)}** days claimed\n"
                "Click a day to see its reward!\n"
                "\u2705 = Claimed | \U0001f4c5 = Today | \U0001f381 = Available | \u2b1b = Unconfigured"
            ),
            color=discord.Color.gold(),
        )
        embed.set_footer(text="\U0001f381 Use /advent claim to claim today's reward!")

        await interaction.response.send_message(embed=embed, view=view)
