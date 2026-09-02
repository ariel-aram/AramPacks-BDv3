from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from ballsdex.core.discord import LayoutView
from bd_models.models import BallInstance, Special
from discord import app_commands
from discord.ext import commands
from discord.ui import ActionRow, Container, Select, TextDisplay

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


class EventSelectView(LayoutView):
    def __init__(self, specials: list[Special], bot: BallsDexBot):
        super().__init__(timeout=120)
        self.specials = specials
        self.bot = bot
        self.current_idx = 0
        self._cont = EventSelectContainer()
        self.add_item(self._cont)
        self._update_buttons()
        self._update_display()

    def _get_current(self) -> Special:
        return self.specials[self.current_idx]

    def _display_text(self) -> str:
        special = self._get_current()
        emoji_display = "\u2753"
        if special.emoji:
            try:
                emoji_obj = self.bot.get_emoji(int(special.emoji))
                emoji_display = str(emoji_obj) if emoji_obj else "\u2753"
            except ValueError, TypeError:
                emoji_display = special.emoji

        return f"## {emoji_display} {special.name}\n**Event #{self.current_idx + 1}** of {len(self.specials)}"

    async def _build_content(self) -> str:
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

        return (
            f"## {emoji_display} {special.name}\n"
            f"**Event #{self.current_idx + 1}** of {len(self.specials)}\n"
            f"\U0001f4c5 {date_range}\n"
            f"\U0001f3b0 Rarity: {rarity_str}\n"
            f"\U0001f4e6 Caught: {card_count} times\n"
            f"\nTotal events: {len(self.specials)}"
        )

    def _update_display(self) -> None:
        special = self._get_current()
        emoji_display = "\u2753"
        if special.emoji:
            try:
                emoji_obj = self.bot.get_emoji(int(special.emoji))
                emoji_display = str(emoji_obj) if emoji_obj else "\u2753"
            except ValueError, TypeError:
                emoji_display = special.emoji
        self._cont.display.content = (
            f"## {emoji_display} {special.name}\n**Event #{self.current_idx + 1}** of {len(self.specials)}"
        )

    async def _update_display_full(self) -> None:
        self._cont.display.content = await self._build_content()

    def _update_buttons(self) -> None:
        self._cont.prev_btn.disabled = self.current_idx == 0
        self._cont.next_btn.disabled = self.current_idx >= len(self.specials) - 1
        if self.specials:
            self._cont._select.options = [
                discord.SelectOption(
                    label=s.name[:100],
                    value=str(i),
                    description=f"Rarity: {s.rarity * 100:.1f}%",
                    emoji="\U0001f4c5",
                )
                for i, s in enumerate(self.specials[:25])
            ]

    async def on_timeout(self) -> None:  # type: ignore[override]
        for child in self.walk_children():
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


class EventSelectContainer(Container):
    nav_row = ActionRow()

    @nav_row.button(label="\u25c0\ufe0f", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        parent = self.view
        assert parent is not None and isinstance(parent, EventSelectView)
        parent.current_idx -= 1
        parent._update_buttons()
        await parent._update_display_full()
        await interaction.response.edit_message(view=parent)

    @nav_row.button(label="\u25b6\ufe0f", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        parent = self.view
        assert parent is not None and isinstance(parent, EventSelectView)
        parent.current_idx += 1
        parent._update_buttons()
        await parent._update_display_full()
        await interaction.response.edit_message(view=parent)

    def __init__(self):
        super().__init__()
        self.display = TextDisplay("Loading...")
        self.add_item(self.display)

        self._select = Select(placeholder="\U0001f4cb Jump to event...")
        self._select.callback = self._on_select
        select_row = ActionRow(self._select)
        self.add_item(select_row)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        parent = self.view
        assert parent is not None and isinstance(parent, EventSelectView)
        try:
            idx = int(self._select.values[0])
            parent.current_idx = idx
        except ValueError, IndexError:
            pass
        parent._update_buttons()
        await parent._update_display_full()
        await interaction.response.edit_message(view=parent)


class Events(commands.Cog):
    """View information about special events with interactive browsing."""

    def __init__(self, bot: BallsDexBot):
        self.bot = bot

    @app_commands.command()
    @app_commands.guild_only()
    async def events(self, interaction: discord.Interaction[BallsDexBot]):
        """Browse all special events with an interactive card viewer."""
        await interaction.response.defer(ephemeral=True)

        specials = [x async for x in Special.objects.order_by("-id").all()]

        if not specials:
            await interaction.followup.send("No special events found in the database.", ephemeral=True)
            return

        view = EventSelectView(specials=specials, bot=self.bot)
        await view._update_display_full()
        await interaction.followup.send(view=view, ephemeral=True)
