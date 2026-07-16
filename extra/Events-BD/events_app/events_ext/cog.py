from typing import TYPE_CHECKING

import discord
from bd_models.models import BallInstance, Special
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


class EventSelectView(discord.ui.View):
    def __init__(self, specials: list[Special], bot: "BallsDexBot"):
        super().__init__(timeout=120)
        self.specials = specials
        self.bot = bot
        self.current_idx = 0
        self._update_buttons()

    def _get_current(self) -> Special:
        return self.specials[self.current_idx]

    def _update_buttons(self) -> None:
        self.prev_btn.disabled = self.current_idx == 0
        self.next_btn.disabled = self.current_idx >= len(self.specials) - 1
        if self.specials:
            self.select_menu.options = [
                discord.SelectOption(
                    label=s.name[:100],
                    value=str(i),
                    description=f"Rarity: {s.rarity * 100:.1f}%",
                    emoji="\U0001f4c5",
                )
                for i, s in enumerate(self.specials[:25])
            ]

    async def _build_embed(self) -> discord.Embed:
        special = self._get_current()
        emoji_display = "\u2753"
        if special.emoji:
            try:
                emoji_obj = self.bot.get_emoji(int(special.emoji))
                emoji_display = str(emoji_obj) if emoji_obj else "\u2753"
            except ValueError, TypeError:
                emoji_display = special.emoji

        rarity_percent = special.rarity * 100
        rarity_str = f"{int(rarity_percent)}%" if rarity_percent.is_integer() else f"{rarity_percent:.2f}%"

        if special.start_date and special.end_date:
            start_ts = f"<t:{int(special.start_date.timestamp())}:f>"
            end_ts = f"<t:{int(special.end_date.timestamp())}:f>"
            date_range = f"{start_ts} \u2014 {end_ts}"
        else:
            date_range = "Ongoing"

        card_count = await BallInstance.objects.filter(special=special).acount()

        embed = discord.Embed(
            title=f"{emoji_display} {special.name}",
            description=(
                f"**Event #{self.current_idx + 1}** of {len(self.specials)}\n"
                f"\U0001f4c5 {date_range}\n"
                f"\U0001f3b0 Rarity: {rarity_str}\n"
                f"\U0001f4e6 Caught: {card_count} times"
            ),
            color=discord.Color.blue(),
        )
        embed.set_footer(text=f"Total events: {len(self.specials)}")
        return embed

    @discord.ui.select(placeholder="\U0001f4cb Jump to event...", row=0)
    async def select_menu(self, interaction: discord.Interaction, select: discord.ui.Select) -> None:
        return

    @discord.ui.button(label="\u25c0\ufe0f", style=discord.ButtonStyle.secondary, row=1)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_idx -= 1
        self._update_buttons()
        embed = await self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="\u25b6\ufe0f", style=discord.ButtonStyle.secondary, row=1)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_idx += 1
        self._update_buttons()
        embed = await self._build_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


@app_commands.guild_only()
class Events(commands.Cog):
    """View information about special events with interactive browsing."""

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot

    @app_commands.command()
    async def events(self, interaction: discord.Interaction["BallsDexBot"]):
        """Browse all special events with an interactive card viewer."""
        await interaction.response.defer(ephemeral=True)

        specials = [x async for x in Special.objects.order_by("-id").all()]

        if not specials:
            await interaction.followup.send("No special events found in the database.", ephemeral=True)
            return

        view = EventSelectView(specials=specials, bot=self.bot)
        embed = await view._build_embed()
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
