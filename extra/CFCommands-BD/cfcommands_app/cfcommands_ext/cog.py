import discord
from ballsdex.core.utils.transformers import BallTransformer
from bd_models.models import Ball
from discord import app_commands
from discord.ext import commands


class CFCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="stats", description="Displays a specific countryball's statistics.")
    async def stats(self, interaction: discord.Interaction, countryball: app_commands.Transform[Ball, BallTransformer]):
        emoji = interaction.client.get_emoji(countryball.emoji_id) or ""

        embed = discord.Embed(
            title=f"{emoji} {countryball.country} Information:",
            description=(
                f"⋄ **Short Name:** {countryball.short_name}\n"
                f"⋄ **Catch Names:** {countryball.catch_names}\n"
                f"⋄ **Regime:** {countryball.regime}\n"
                f"⋄ **Economy:** {countryball.economy}\n"
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
