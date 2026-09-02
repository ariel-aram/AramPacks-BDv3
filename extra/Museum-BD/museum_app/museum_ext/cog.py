from __future__ import annotations

from typing import TYPE_CHECKING, override

import discord
from ballsdex.core.discord import LayoutView
from ballsdex.core.discord import Modal as BallsDexModal
from bd_models.models import BallInstance
from discord import app_commands
from discord.ext import commands
from discord.ui import ActionRow, Container, TextDisplay, TextInput

from ..models import MuseumCard

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


class MuseumPaginatorView(LayoutView):
    def __init__(self, cards: list[str], target_name: str, timeout: int = 120):
        super().__init__(timeout=timeout)
        self.cards = cards
        self.target_name = target_name
        self.current_page = 0
        self._cont = MuseumPaginatorContainer()
        self.add_item(self._cont)
        self._update_display()
        self._update_buttons()

    def _update_buttons(self) -> None:
        self._cont.prev_btn.disabled = self.current_page == 0
        self._cont.next_btn.disabled = self.current_page >= len(self.cards) - 1
        self._cont.page_label.label = f"{self.current_page + 1} / {len(self.cards)}"

    def _update_display(self) -> None:
        card_id = self.cards[self.current_page]
        content = (
            f"## \U0001f3db\ufe0f {self.target_name}'s Museum \u2014 Card {self.current_page + 1}/{len(self.cards)}\n"
            f"\U0001f5bc\ufe0f Displayed Card ID: `{card_id}`\n"
            f"\n*Use the buttons below to navigate between cards.*"
        )
        for child in self._cont.walk_children():
            if isinstance(child, TextDisplay):
                child.content = content

    async def on_timeout(self) -> None:  # type: ignore[override]
        for child in self.walk_children():
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


class MuseumPaginatorContainer(Container):
    display = TextDisplay("Loading...")
    btn_row = ActionRow()

    @btn_row.button(label="\u25c0\ufe0f", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        parent = self.view
        assert parent is not None and isinstance(parent, MuseumPaginatorView)
        if parent.current_page > 0:
            parent.current_page -= 1
            parent._update_buttons()
            parent._update_display()
            await interaction.response.edit_message(view=parent)

    @btn_row.button(label="1 / 1", style=discord.ButtonStyle.gray, disabled=True)
    async def page_label(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        pass

    @btn_row.button(label="\u25b6\ufe0f", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        parent = self.view
        assert parent is not None and isinstance(parent, MuseumPaginatorView)
        if parent.current_page < len(parent.cards) - 1:
            parent.current_page += 1
            parent._update_buttons()
            parent._update_display()
            await interaction.response.edit_message(view=parent)


class MuseumEditModal(BallsDexModal):
    def __init__(self, current_cards: list[str]):
        super().__init__(title="\U0001f3db\ufe0f Edit Museum Display")
        self.card_input = TextInput(
            label="Card IDs (comma-separated, max 3)",
            placeholder="e.g. ABC123, DEF456, GHI789",
            default=", ".join(current_cards) if current_cards else "",
            required=False,
            max_length=300,
            style=discord.TextStyle.paragraph,
        )
        self.add_item(self.card_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:  # type: ignore[override]
        await interaction.response.defer(ephemeral=True)
        raw = self.card_input.value.strip()
        if not raw:
            await interaction.followup.send("\u26a0\ufe0f You must specify at least one card ID.", ephemeral=True)
            return

        cards = [c.strip() for c in raw.split(",") if c.strip()]
        if len(cards) > 3:
            await interaction.followup.send("\u26a0\ufe0f You can only display up to **3 cards**.", ephemeral=True)
            return
        if len(set(cards)) != len(cards):
            await interaction.followup.send(
                "\u26a0\ufe0f You can't display the same card more than once.", ephemeral=True
            )
            return
        for c in cards:
            try:
                pk = int(c, 16)
            except ValueError:
                await interaction.followup.send(f"\u26a0\ufe0f Invalid card ID format: `{c}`", ephemeral=True)
                return

            try:
                instance = await BallInstance.objects.select_related("player").aget(pk=pk)
            except BallInstance.DoesNotExist:
                await interaction.followup.send(f"\u26a0\ufe0f Card `{c}` doesn't exist.", ephemeral=True)
                return

            if instance.player.discord_id != interaction.user.id:
                await interaction.followup.send(f"\u26a0\ufe0f Card `{c}` doesn't belong to you.", ephemeral=True)
                return

        await set_museum_cards(interaction.user.id, cards)
        await interaction.followup.send(
            "\u2705 Museum Updated\nYour museum now displays:\n" + "\n".join(f"- `{c}`" for c in cards),
            ephemeral=True,
        )


async def get_museum_cards(user_id: int) -> list[str]:
    return [
        card_id
        async for card_id in MuseumCard.objects.filter(user_id=user_id)
        .order_by("position")
        .values_list("card_id", flat=True)
    ]


async def set_museum_cards(user_id: int, cards: list[str]) -> None:
    await MuseumCard.objects.filter(user_id=user_id).adelete()
    await MuseumCard.objects.abulk_create(
        [MuseumCard(user_id=user_id, card_id=card_id, position=i) for i, card_id in enumerate(cards, 1)]
    )


class Museum(commands.Cog):
    """A cog for managing users' museum displays with interactive components."""

    def __init__(self, bot: BallsDexBot):
        self.bot = bot

    async def send_error(self, interaction: discord.Interaction, message: str):
        await interaction.response.send_message(f"\u26a0\ufe0f Error\n{message}", ephemeral=True)

    @app_commands.command(name="museum_view", description="View someone's museum display with interactive pagination.")
    @app_commands.describe(user="The user whose museum you want to view.")
    async def museum_view(self, interaction: discord.Interaction, user: discord.User | None = None):
        try:
            target: discord.User | discord.Member = user or interaction.user
            cards = await get_museum_cards(target.id)

            if not cards:
                await interaction.response.send_message(
                    f"{target.display_name} has no cards displayed in their museum!", ephemeral=True
                )
                return

            view = MuseumPaginatorView(cards=cards, target_name=target.display_name)
            await interaction.response.send_message(view=view)

        except discord.Forbidden:
            await self.send_error(interaction, "I don't have permission to use components here.")
        except discord.HTTPException as e:
            await self.send_error(interaction, f"Discord API error occurred: `{e}`")
        except Exception as e:
            await self.send_error(interaction, f"An unexpected error occurred: `{type(e).__name__}` \u2014 {e}")

    @app_commands.command(name="museum_edit", description="Edit your museum display via a modal form.")
    @app_commands.checks.cooldown(1, 15, key=lambda i: i.user.id)
    async def museum_edit(self, interaction: discord.Interaction):
        try:
            current_cards = await get_museum_cards(interaction.user.id)
            modal = MuseumEditModal(current_cards=current_cards)
            await interaction.response.send_modal(modal)

        except Exception as e:
            await self.send_error(interaction, f"Unexpected error: `{type(e).__name__}` \u2014 {e}")

    @override
    async def cog_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        if isinstance(error, app_commands.CommandOnCooldown):
            await interaction.response.send_message(
                f"\u23f3 You're editing too fast! Try again in `{error.retry_after:.1f}` seconds.", ephemeral=True
            )
            return
        await self.send_error(interaction, f"Unexpected error: `{type(error).__name__}` \u2014 {error}")
