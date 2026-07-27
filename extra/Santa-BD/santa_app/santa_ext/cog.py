from __future__ import annotations

import contextlib
import random
from typing import TYPE_CHECKING

import discord
from ballsdex.core.discord import LayoutView
from ballsdex.core.utils.utils import is_staff
from ballsdex.settings import settings
from bd_models.models import Ball, BallInstance, BlacklistedID, Player
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import ActionRow, Container, TextDisplay

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


class SantaConfirmContainer(Container):
    display = TextDisplay("")
    btn_row = ActionRow()

    @btn_row.button(label="\u2705 Deliver Gifts!", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        view = self.view
        assert view is not None
        view.value = True
        self.clear_items()
        await interaction.response.edit_message(content="\U0001f381 Santa is on his way...", view=None)

    @btn_row.button(label="\u274c Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        view = self.view
        assert view is not None
        view.value = False
        self.clear_items()
        await interaction.response.edit_message(content="Santa delivery cancelled.", view=None)


class SantaConfirmView(LayoutView):
    container: SantaConfirmContainer = SantaConfirmContainer()

    def __init__(self):
        super().__init__(timeout=30)
        self.value: bool | None = None

    async def on_timeout(self) -> None:  # type: ignore[override]
        self.value = False


class SantaMail(commands.Cog):
    def __init__(self, bot: BallsDexBot) -> None:
        self.bot = bot
        self.santa_loop.start()

    def cog_unload(self):  # type: ignore[override]
        self.santa_loop.cancel()

    async def _get_blacklist(self):
        return {b.discord_id async for b in BlacklistedID.objects.all()}

    @tasks.loop(hours=24)
    async def santa_loop(self):
        balls = [ball async for ball in Ball.enabled_objects.all()]
        players = [player async for player in Player.objects.all()]

        if not balls or not players:
            return

        blacklist = await self._get_blacklist()
        eligible = [p for p in players if p.discord_id not in blacklist]
        if not eligible:
            return

        chosen_players = random.sample(eligible, min(5, len(eligible)))

        for player in chosen_players:
            ball = random.choice(balls)
            await BallInstance.objects.acreate(ball=ball, player=player)

            user = self.bot.get_user(player.discord_id)
            if user is None:
                try:
                    user = await self.bot.fetch_user(player.discord_id)
                except discord.NotFound:
                    continue

            emoji = self.bot.get_emoji(ball.emoji_id) if ball.emoji_id else ""
            ball_name = f"{emoji} {ball.country}" if emoji else ball.country

            embed = discord.Embed(
                title="\U0001f384 Santa's Mail",
                description=(
                    f"Ho ho ho! You've been chosen by Santa! You received a {ball_name} {settings.collectible_name}!"
                ),
                color=discord.Color.red(),
            )
            embed.set_footer(text="Happy holidays from Santa \U0001f384")

            with contextlib.suppress(discord.Forbidden):
                await user.send(embed=embed)

    @santa_loop.before_loop
    async def before_santa_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="santamail", description="Force Santa to deliver gifts right now.")
    async def santamail(self, interaction: discord.Interaction[BallsDexBot]):
        if not await is_staff(interaction):
            await interaction.response.send_message("You are not allowed to use this command.", ephemeral=True)
            return

        balls = [ball async for ball in Ball.enabled_objects.all()]
        players = [player async for player in Player.objects.all()]

        if not balls or not players:
            await interaction.response.send_message("No balls or players available.", ephemeral=True)
            return

        blacklist = await self._get_blacklist()
        eligible = [p for p in players if p.discord_id not in blacklist]
        if not eligible:
            await interaction.response.send_message("No eligible players found.", ephemeral=True)
            return

        count_to_send = min(5, len(eligible))

        content = (
            "## \U0001f384 Force Santa Delivery\n"
            f"This will deliver **{count_to_send}** {settings.plural_collectible_name} "
            f"to {count_to_send} random eligible players.\n"
            "*\u23f0 This confirmation expires in 30 seconds.*"
        )

        view = SantaConfirmView()
        await interaction.response.send_message(content=content, view=view, ephemeral=True)  # type: ignore[arg-type]
        await view.wait()

        if view.value is None or view.value is False:
            return

        chosen_players = random.sample(eligible, count_to_send)
        gifts_sent = 0
        for player in chosen_players:
            ball = random.choice(balls)
            await BallInstance.objects.acreate(ball=ball, player=player)
            gifts_sent += 1

        await interaction.edit_original_response(
            content=f"\u2705 Santa delivered **{gifts_sent}** {settings.plural_collectible_name} today!"
        )
