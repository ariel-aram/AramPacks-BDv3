import logging
import random
from typing import cast

import discord
from ballsdex.core.bot import BallsDexBot  # noqa: TC002
from ballsdex.core.utils.buttons import ConfirmChoiceView
from ballsdex.core.utils.transformers import BallInstanceTransformer  # noqa: TC002
from bd_models.models import Ball, BallInstance, Player, TradeObject
from discord import app_commands
from discord.ext import commands

log = logging.getLogger("ballsdex.packages.exchange")


@app_commands.guild_only()
class Exchange(commands.Cog):
    """Exchange one of your owned balls for a random new one."""

    def __init__(self, bot: BallsDexBot):
        self.bot = bot
        self.cooldowns = {}

    @app_commands.command(name="exchange", description="Exchange one of your balls for a random new one.")
    @app_commands.describe(countryball="Select a ball from your collection to exchange.")
    async def exchange(
        self,
        interaction: discord.Interaction[BallsDexBot],
        countryball: app_commands.Transform[BallInstance, BallInstanceTransformer],
    ):
        user_id = interaction.user.id
        now = discord.utils.utcnow().timestamp()

        if user_id in self.cooldowns and now - self.cooldowns[user_id] < 30:
            remaining = 30 - int(now - self.cooldowns[user_id])
            await interaction.response.send_message(f"\u23f3 You can exchange again in {remaining}s.", ephemeral=True)
            return
        self.cooldowns[user_id] = now

        player, _ = await Player.objects.aget_or_create(discord_id=user_id)
        chosen = await BallInstance.objects.filter(id=countryball.id, player=player).select_related("ball").afirst()  # type: ignore[attr-defined]
        if chosen is None:
            await interaction.response.send_message("\u274c You don\u2019t own that ball.", ephemeral=True)
            return

        confirm_view = ConfirmChoiceView(interaction)
        await interaction.response.send_message(
            "Are you sure you want to exchange "
            f"**{getattr(chosen.ball, 'country', getattr(chosen.ball, 'name', 'Unknown'))}**?",
            view=confirm_view,
        )
        await confirm_view.wait()
        if not confirm_view.value:
            return

        enabled_balls = [b async for b in Ball.enabled_objects.all()]
        if not enabled_balls:
            await interaction.followup.send("\u26a0\ufe0f No enabled balls found.")
            return

        new_ball = random.choice(enabled_balls)
        atk_bonus = random.randint(-20, 20)
        hp_bonus = random.randint(-20, 20)

        try:
            await TradeObject.objects.filter(ballinstance_id=chosen.id).adelete()  # type: ignore[attr-defined]
            await BallInstance.objects.acreate(
                player=player,
                ball=new_ball,
                attack_bonus=atk_bonus,
                health_bonus=hp_bonus,
            )
            await chosen.adelete()
        except Exception as e:
            log.error("Exchange failed", exc_info=e)
            await interaction.followup.send(f"\u274c Exchange failed: {e}")
            return

        old_name = getattr(chosen.ball, "country", getattr(chosen.ball, "name", "Unknown"))
        new_name = getattr(new_ball, "country", getattr(new_ball, "name", "Unknown"))
        emoji = self.bot.get_emoji(cast("int", getattr(new_ball, "emoji_id", None))) or "\U0001f3b2"

        embed = discord.Embed(
            title="Exchange Complete!",
            description=f"**{interaction.user.display_name}** exchanged **{old_name}** for {emoji} **{new_name}**!",
            color=discord.Color.gold(),
        )
        embed.add_field(name="New Stats", value=f"ATK {atk_bonus:+}% | HP {hp_bonus:+}%")
        embed.set_footer(text="A fair trade... or was it?")

        await interaction.followup.send(embed=embed)
