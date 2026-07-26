from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from ballsdex.core.discord import LayoutView
from discord import app_commands
from discord.ext import commands
from discord.ui import Container, TextDisplay

from cardstudio_app.models import CardConfig

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


class CardStudio(commands.Cog):
    """Card Studio configuration viewer."""

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot

    @app_commands.command(name="cardstudio", description="Show the current card studio configuration.")
    @app_commands.guild_only()
    async def cardstudio(self, interaction: discord.Interaction):
        config = await CardConfig.objects.afirst()
        if config is None or not config.enabled:
            await interaction.response.send_message("Card Studio is disabled.", ephemeral=True)
            return

        summary = (
            "## Card Studio\n"
            f"Status: **enabled**\n"
            f"Title: {config.title_size}px at ({config.title_x}, {config.title_y})\n"
            f"Ability name: {config.capacity_name_size}px at ({config.capacity_name_x}, {config.capacity_name_y})\n"
            f"Ability description: {config.capacity_description_size}px at ({config.capacity_description_x},"
            f" {config.capacity_description_y})\n"
            f"Stats: {config.stats_size}px at health ({config.health_x}, {config.health_y}),"
            f" attack ({config.attack_x}, {config.attack_y})\n"
            f"Credits: {config.credits_size}px at ({config.credits_x}, {config.credits_y})\n"
            f"Artwork: ({config.artwork_x1}, {config.artwork_y1}) to"
            f" ({config.artwork_x2}, {config.artwork_y2})\n"
            f"Icon: {config.icon_size}px at ({config.icon_x}, {config.icon_y})"
        )

        view = LayoutView()
        container = Container()
        view.add_item(container)
        container.add_item(TextDisplay(summary))
        await interaction.response.send_message(view=view, ephemeral=True)
