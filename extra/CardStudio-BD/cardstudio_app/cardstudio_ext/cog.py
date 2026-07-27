from __future__ import annotations

from typing import TYPE_CHECKING

from discord.ext import commands

from cardstudio_app.image_gen import apply_patches
from cardstudio_app.models import CardConfig

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


class CardStudio(commands.Cog):
    """Card Studio configuration management."""

    def __init__(self, bot: BallsDexBot):
        self.bot = bot

    @commands.command(name="reloadcardstudio")
    @commands.is_owner()
    async def reload_cardstudio(self, ctx: commands.Context) -> None:
        """Re-apply the Card Studio draw_card patch with current database config."""
        apply_patches()
        config = CardConfig.get_config()
        if config is None or not config.enabled:
            await ctx.send("Card Studio is disabled.")
            return

        await ctx.send(
            "\u2705 Card Studio reloaded.\n"
            f"Status: **enabled**\n"
            f"Title: {config.title_size}px at ({config.title_x}, {config.title_y})\n"
            f"Stats: {config.stats_size}px — "
            f"HP ({config.health_x}, {config.health_y}) "
            f"ATK ({config.attack_x}, {config.attack_y})\n"
            f"Artwork: ({config.artwork_x1}, {config.artwork_y1}) to"
            f" ({config.artwork_x2}, {config.artwork_y2})"
        )
