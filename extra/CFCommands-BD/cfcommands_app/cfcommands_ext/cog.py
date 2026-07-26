from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot
    from ballsdex.core.utils.transformers import BallTransformer
    from bd_models.models import Ball


class CFCommands(commands.Cog):
    def __init__(self, bot: BallsDexBot) -> None:
        self.bot = bot

    @app_commands.command(name="stats", description="Displays a specific countryball's statistics.")
    async def stats(self, interaction: discord.Interaction, countryball: app_commands.Transform[Ball, BallTransformer]):
        emoji = interaction.client.get_emoji(countryball.emoji_id) or ""

        embed = discord.Embed(
            title=f"{emoji} {countryball.country} Information:",
            description=(
                f"⋄ **Short Name:** {countryball.short_name}\n"
                f"⋄ **Catch Names:** {countryball.catch_names}\n"
                f"⋄ **Regime:** {countryball.cached_regime}\n"
                f"⋄ **Economy:** {countryball.cached_economy}\n"
                f"⋄ **Rarity:** {countryball.rarity}\n"
                f"⋄ **Attack:** {countryball.attack}\n"
                f"⋄ **Health:** {countryball.health}\n"
                f"⋄ **Capacity Name:** {countryball.capacity_name}\n"
                f"⋄ **Capacity Description:** {countryball.capacity_description}\n"
                f"⋄ **Image Credits:** {countryball.credits}\n"
            ),
            color=discord.Color.blurple(),
        )
        await interaction.response.send_message(embed=embed)
