from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import discord
from ballsdex.core.discord import LayoutView
from bd_models.models import Player
from discord import app_commands
from discord.ext import commands
from discord.ui import Container, TextDisplay

from codes_app.models import PromoCode

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

log = logging.getLogger("codes")


class CodesCog(commands.Cog):
    """Promo code redemption system."""

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot

    @app_commands.command(name="redeem", description="Redeem a promo code.")
    @app_commands.describe(code="The promo code to redeem.")
    @app_commands.guild_only()
    async def redeem(self, interaction: discord.Interaction, code: str):
        cleaned = code.strip().upper()
        if not cleaned:
            await self._send_result(interaction, "Please provide a promo code.", success=False)
            return

        player, _ = await Player.objects.aget_or_create(discord_id=interaction.user.id)
        promo = await PromoCode.objects.filter(code__iexact=cleaned).afirst()
        if promo is None:
            await self._send_result(interaction, "That promo code does not exist.", success=False)
            return

        success, message = await promo.redeem(player, bot=self.bot)
        await self._send_result(interaction, message, success=success)

    async def _send_result(
        self,
        interaction: discord.Interaction,
        message: str,
        *,
        success: bool,
    ):
        view = LayoutView()
        container = Container()
        view.add_item(container)

        emoji = "\N{WHITE HEAVY CHECK MARK}" if success else "\N{CROSS MARK}"
        container.add_item(TextDisplay(f"## {emoji} Promo code"))
        container.add_item(TextDisplay(message))

        if interaction.response.is_done():
            await interaction.followup.send(view=view, ephemeral=True)
        else:
            await interaction.response.send_message(view=view, ephemeral=True)
