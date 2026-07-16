from typing import TYPE_CHECKING, Optional

import discord
from asgiref.sync import sync_to_async
from discord import app_commands
from discord.ext import commands

from ..models import MuseumCard

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


class MuseumPaginatorView(discord.ui.View):
    def __init__(self, embeds: list[discord.Embed], timeout: int = 120):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0
        self._update_buttons()

    def _update_buttons(self) -> None:
        self.prev_btn.disabled = self.current_page == 0
        self.next_btn.disabled = self.current_page >= len(self.embeds) - 1
        self.page_label.label = f"{self.current_page + 1} / {len(self.embeds)}"

    @discord.ui.button(label="\u25c0\ufe0f", style=discord.ButtonStyle.secondary)
    async def prev_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_page = (self.current_page - 1) % len(self.embeds)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    @discord.ui.button(label="1 / 1", style=discord.ButtonStyle.gray, disabled=True)
    async def page_label(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        pass

    @discord.ui.button(label="\u25b6\ufe0f", style=discord.ButtonStyle.secondary)
    async def next_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.current_page = (self.current_page + 1) % len(self.embeds)
        self._update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def on_timeout(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


class MuseumEditModal(discord.ui.Modal):
    def __init__(self, current_cards: list[str]):
        super().__init__(title="\U0001f3db\ufe0f Edit Museum Display")
        self.card_input = discord.ui.TextInput(
            label="Card IDs (comma-separated, max 3)",
            placeholder="e.g. ABC123, DEF456, GHI789",
            default=", ".join(current_cards) if current_cards else "",
            required=False,
            max_length=300,
            style=discord.TextStyle.paragraph,
        )
        self.add_item(self.card_input)

    async def on_submit(self, interaction: discord.Interaction) -> None:
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
            if not c.isalnum():
                await interaction.followup.send(f"\u26a0\ufe0f Invalid card ID format: `{c}`", ephemeral=True)
                return

        await set_museum_cards(interaction.user.id, cards)
        embed = discord.Embed(
            title="\u2705 Museum Updated",
            description="Your museum now displays:\n" + "\n".join(f"- `{c}`" for c in cards),
            colour=discord.Colour.green(),
        )
        await interaction.followup.send(embed=embed, ephemeral=True)


@sync_to_async
def get_museum_cards(user_id: int) -> list[str]:
    return list(MuseumCard.objects.filter(user_id=user_id).order_by("position").values_list("card_id", flat=True))


@sync_to_async
def set_museum_cards(user_id: int, cards: list[str]) -> None:
    MuseumCard.objects.filter(user_id=user_id).delete()
    for i, card_id in enumerate(cards, 1):
        MuseumCard.objects.create(user_id=user_id, card_id=card_id, position=i)


class Museum(commands.Cog):
    """A cog for managing users' museum displays with interactive components."""

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot

    async def send_error(self, interaction: discord.Interaction, message: str):
        embed = discord.Embed(title="\u26a0\ufe0f Error", description=message, colour=discord.Colour.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="museum_view", description="View someone's museum display with interactive pagination.")
    @app_commands.describe(user="The user whose museum you want to view.")
    async def museum_view(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        try:
            target: discord.User | discord.Member = user or interaction.user
            cards = await get_museum_cards(target.id)

            if not cards:
                await interaction.response.send_message(
                    f"{target.display_name} has no cards displayed in their museum!", ephemeral=True
                )
                return

            embeds = []
            for i, card_id in enumerate(cards, start=1):
                embed = discord.Embed(
                    title=f"\U0001f3db\ufe0f {target.display_name}'s Museum \u2014 Card {i}/{len(cards)}",
                    description=f"\U0001f5bc\ufe0f Displayed Card ID: `{card_id}`",
                    colour=discord.Colour.gold(),
                )
                embed.set_footer(text="Use the buttons below to navigate between cards.")
                embeds.append(embed)

            view = MuseumPaginatorView(embeds)
            await interaction.response.send_message(embed=embeds[0], view=view)

        except discord.Forbidden:
            await self.send_error(interaction, "I don't have permission to send embeds or use components here.")
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

        except app_commands.CommandOnCooldown as e:
            await interaction.response.send_message(
                f"\u23f3 You're editing too fast! Try again in `{e.retry_after:.1f}` seconds.", ephemeral=True
            )
        except Exception as e:
            await self.send_error(interaction, f"Unexpected error: `{type(e).__name__}` \u2014 {e}")
