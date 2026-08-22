from __future__ import annotations

import contextlib
import random
from typing import TYPE_CHECKING

import discord
from ballsdex.core.discord import LayoutView
from ballsdex.core.utils.utils import is_staff
from bd_models.models import Ball, BallInstance, BlacklistedID, Player
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import ActionRow, Button, Container, TextDisplay
from django.utils import timezone
from settings.models import settings

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


class SantaConfirmContainer(Container):
    def __init__(self, text: str):
        super().__init__()
        self.display = TextDisplay(text)
        self.add_item(self.display)
        self.btn_row = ActionRow()

        confirm_btn = Button(label="\u2705 Deliver Gifts!", style=discord.ButtonStyle.green)
        confirm_btn.callback = self.confirm
        cancel_btn = Button(label="\u274c Cancel", style=discord.ButtonStyle.red)
        cancel_btn.callback = self.cancel

        self.btn_row.add_item(confirm_btn)
        self.btn_row.add_item(cancel_btn)
        self.add_item(self.btn_row)

    async def confirm(self, interaction: discord.Interaction) -> None:
        view = self.view
        if isinstance(view, SantaConfirmView):
            view.value = True
            self.display.content = "\U0001f381 Santa is on his way..."
            self.btn_row.clear_items()
            await interaction.response.edit_message(view=view)

    async def cancel(self, interaction: discord.Interaction) -> None:
        view = self.view
        if isinstance(view, SantaConfirmView):
            view.value = False
            self.display.content = "Santa delivery cancelled."
            self.btn_row.clear_items()
            await interaction.response.edit_message(view=view)


class SantaConfirmView(LayoutView):
    def __init__(self, content: str):
        super().__init__(timeout=30)
        self.value: bool | None = None
        self._cont = SantaConfirmContainer(content)
        self.add_item(self._cont)

    async def on_timeout(self) -> None:  # type: ignore[override]
        self.value = False


class SantaMail(commands.Cog):
    def __init__(self, bot: BallsDexBot) -> None:
        self.bot = bot
        self.santa_loop.start()

    def cog_unload(self):  # type: ignore[override]
        self.santa_loop.cancel()

    async def _get_blacklist(self) -> set[int]:
        return {b.discord_id async for b in BlacklistedID.objects.all()}

    async def _get_random_eligible_players(self, count: int = 5) -> list[Player]:
        blacklist = await self._get_blacklist()
        qs = Player.objects.exclude(discord_id__in=blacklist)
        total = await qs.acount()
        if total == 0:
            return []

        if total <= count:
            return [p async for p in qs]

        pks = [pk async for pk in qs.values_list("id", flat=True)]
        chosen_pks = random.sample(pks, count)
        return [p async for p in Player.objects.filter(id__in=chosen_pks)]

    @tasks.loop(hours=24)
    async def santa_loop(self):
        balls = [ball async for ball in Ball.enabled_objects.all()]
        if not balls:
            return

        chosen_players = await self._get_random_eligible_players(5)
        if not chosen_players:
            return

        now = timezone.now()

        for player in chosen_players:
            ball = random.choice(balls)
            atk_bonus = random.randint(-settings.max_attack_bonus, settings.max_attack_bonus)
            hp_bonus = random.randint(-settings.max_health_bonus, settings.max_health_bonus)

            await BallInstance.objects.acreate(
                ball=ball,
                player=player,
                attack_bonus=atk_bonus,
                health_bonus=hp_bonus,
                catch_date=now,
            )

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
        if not balls:
            await interaction.response.send_message("No balls available.", ephemeral=True)
            return

        chosen_players = await self._get_random_eligible_players(5)
        if not chosen_players:
            await interaction.response.send_message("No eligible players found.", ephemeral=True)
            return

        count_to_send = len(chosen_players)

        content = (
            "## \U0001f384 Force Santa Delivery\n"
            f"This will deliver **{count_to_send}** {settings.plural_collectible_name} "
            f"to {count_to_send} random eligible players.\n"
            "*\u23f0 This confirmation expires in 30 seconds.*"
        )

        view = SantaConfirmView(content)
        await interaction.response.send_message(view=view, ephemeral=True)
        await view.wait()

        if view.value is None or view.value is False:
            return

        now = timezone.now()
        gifts_sent = 0
        for player in chosen_players:
            ball = random.choice(balls)
            atk_bonus = random.randint(-settings.max_attack_bonus, settings.max_attack_bonus)
            hp_bonus = random.randint(-settings.max_health_bonus, settings.max_health_bonus)

            await BallInstance.objects.acreate(
                ball=ball,
                player=player,
                attack_bonus=atk_bonus,
                health_bonus=hp_bonus,
                catch_date=now,
            )
            gifts_sent += 1

        await interaction.edit_original_response(
            content=f"\u2705 Santa delivered **{gifts_sent}** {settings.plural_collectible_name} today!"
        )
