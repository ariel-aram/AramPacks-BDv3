import discord
from ballsdex.core.bot import BallsDexBot  # noqa: TC002
from ballsdex.core.discord import LayoutView
from ballsdex.core.utils.transformers import BallTransformer  # noqa: TC002
from bd_models.models import Ball, BallInstance
from discord import app_commands
from discord.ext import commands
from discord.ui import ActionRow, Button, Container, Select, TextDisplay
from django.core.exceptions import ObjectDoesNotExist

from ..models import WishlistItem


class WishlistManageView(LayoutView):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id
        self._cont = WishlistManageContainer()
        self.add_item(self._cont)

    async def _get_wishlist_data(self) -> list[dict[str, str]]:
        items = [item async for item in WishlistItem.objects.filter(user_id=self.user_id)]
        result = []
        for item in items:
            ball = await Ball.objects.filter(country__iexact=item.ball_country).afirst()
            owned = (
                await BallInstance.objects.filter(player__discord_id=self.user_id, ball=ball).acount() if ball else 0
            )
            result.append({"country": ball.country if ball else item.ball_country, "owned": str(owned)})
        return result

    def _build_content(self) -> str:
        return "Loading..."  # replaced by _refresh_select

    async def _refresh_select(self) -> None:
        data = await self._get_wishlist_data()
        options = []
        for item in data:
            options.append(
                discord.SelectOption(
                    label=item["country"][:100],
                    value=item["country"],
                    description=f"Owned: {item['owned']}",
                    emoji="\U0001f381",
                )
            )
        if not options:
            options = [discord.SelectOption(label="No items in wishlist", value="_none", default=True)]
            content = "## \U0001f381 Wishlist\nYour wishlist is empty."
        else:
            lines = [f"{item['country']} ({item['owned']} owned)" for item in data]
            content = "## \U0001f381 Your Wishlist\n" + "\n".join(lines) + f"\n\n*{len(data)} item(s) on your wishlist*"

        self._cont.manage_select.options = options
        self._cont.display.content = content

    async def on_timeout(self) -> None:  # type: ignore[override]
        for child in self.walk_children():
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


class WishlistManageContainer(Container):
    def __init__(self):
        super().__init__()
        self.display = TextDisplay("Loading...")
        self.add_item(self.display)

        self.manage_select = Select(placeholder="\u2795 Manage wishlist...")
        self.manage_select.callback = self._on_select
        select_row = ActionRow(self.manage_select)
        self.add_item(select_row)

        self.btn_row = ActionRow()
        self.remove_btn = Button(label="\U0001f5d1\ufe0f Remove Selected", style=discord.ButtonStyle.danger)
        self.remove_btn.callback = self._remove
        self.purge_btn = Button(label="\u274c Purge All", style=discord.ButtonStyle.secondary)
        self.purge_btn.callback = self._purge
        self.btn_row.add_item(self.remove_btn)
        self.btn_row.add_item(self.purge_btn)
        self.add_item(self.btn_row)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        pass

    async def _remove(self, interaction: discord.Interaction) -> None:
        parent = self.view
        assert parent is not None and isinstance(parent, WishlistManageView)
        values = self.manage_select.values
        if not values or values[0] == "_none":
            await interaction.response.send_message("Select an item to remove first.", ephemeral=True)
            return

        country = values[0]
        try:
            item = await WishlistItem.objects.aget(user_id=parent.user_id, ball_country=country)
            await item.adelete()
        except ObjectDoesNotExist:
            await interaction.response.send_message("Item not found in your wishlist.", ephemeral=True)
            return

        await parent._refresh_select()
        self.display.content += f"\n\n\u2705 Removed {country} from your wishlist"
        await interaction.response.edit_message(view=parent)

    async def _purge(self, interaction: discord.Interaction) -> None:
        parent = self.view
        assert parent is not None and isinstance(parent, WishlistManageView)
        items = WishlistItem.objects.filter(user_id=parent.user_id)
        count = await items.acount()
        if count == 0:
            await interaction.response.send_message("Your wishlist is already empty.", ephemeral=True)
            return

        confirm_view = PurgeConfirmView(parent, f"Delete all **{count}** items from your wishlist?")
        await interaction.response.send_message(
            view=confirm_view,
            ephemeral=True,
        )


class PurgeConfirmView(LayoutView):
    def __init__(self, parent: WishlistManageView, text: str):
        super().__init__(timeout=15)
        self.parent = parent
        self._cont = PurgeConfirmContainer(text)
        self.add_item(self._cont)


class PurgeConfirmContainer(Container):
    def __init__(self, text: str):
        super().__init__()
        self.display = TextDisplay(text)
        self.add_item(self.display)
        self.btn_row = ActionRow()

        confirm_btn = Button(label="\u2705 Yes, Purge All", style=discord.ButtonStyle.danger)
        confirm_btn.callback = self.confirm
        cancel_btn = Button(label="\u274c Cancel", style=discord.ButtonStyle.secondary)
        cancel_btn.callback = self.cancel

        self.btn_row.add_item(confirm_btn)
        self.btn_row.add_item(cancel_btn)
        self.add_item(self.btn_row)

    async def confirm(self, interaction: discord.Interaction) -> None:
        parent = self.view
        assert parent is not None and isinstance(parent, PurgeConfirmView)
        items = WishlistItem.objects.filter(user_id=parent.parent.user_id)
        await items.adelete()
        self.display.content = "\u2705 Wishlist cleared."
        self.btn_row.clear_items()
        await interaction.response.edit_message(view=parent)

    async def cancel(self, interaction: discord.Interaction) -> None:
        parent = self.view
        self.display.content = "Purge cancelled."
        self.btn_row.clear_items()
        await interaction.response.edit_message(view=parent)


@app_commands.guild_only()
class Wishlist(commands.GroupCog, group_name="wishlist"):
    def __init__(self, bot: BallsDexBot) -> None:
        self.bot = bot

    @app_commands.command(name="view", description="View and manage your wishlist interactively.")
    async def view(self, interaction: discord.Interaction, user: discord.User | None = None):
        target = user or interaction.user
        target_id = target.id

        if target_id != interaction.user.id:
            items = [item async for item in WishlistItem.objects.filter(user_id=target_id)]
            if not items:
                await interaction.response.send_message(f"{target.display_name}'s wishlist is empty.", ephemeral=True)
                return
            lines = []
            for item in items:
                ball = await Ball.objects.filter(country__iexact=item.ball_country).afirst()
                owned = (
                    await BallInstance.objects.filter(player__discord_id=target_id, ball=ball).acount() if ball else 0
                )
                lines.append(f"{ball.country if ball else item.ball_country} ({owned} owned)")
            await interaction.response.send_message(f"## {target.display_name}'s Wishlist\n" + "\n".join(lines))
            return

        view = WishlistManageView(user_id=interaction.user.id)
        await view._refresh_select()
        await interaction.response.send_message(view=view, ephemeral=True)

    @app_commands.command(name="add", description="Add a countryball to your wishlist.")
    async def add(self, interaction: discord.Interaction, countryball: app_commands.Transform[Ball, BallTransformer]):
        exists = await WishlistItem.objects.filter(
            user_id=interaction.user.id, ball_country=countryball.country
        ).aexists()

        if exists:
            await interaction.response.send_message(
                f"{countryball.country} is already in your wishlist.", ephemeral=True
            )
            return

        await WishlistItem.objects.acreate(user_id=interaction.user.id, ball_country=countryball.country)
        await interaction.response.send_message(
            f"\u2705 Added **{countryball.country}** to your wishlist!", ephemeral=True
        )

    @app_commands.command(name="remove", description="Remove a countryball from your wishlist.")
    async def remove(
        self, interaction: discord.Interaction, countryball: app_commands.Transform[Ball, BallTransformer]
    ):
        try:
            item = await WishlistItem.objects.aget(user_id=interaction.user.id, ball_country=countryball.country)
        except ObjectDoesNotExist:
            await interaction.response.send_message(f"{countryball.country} is not in your wishlist.", ephemeral=True)
            return

        await item.adelete()
        await interaction.response.send_message(
            f"\u2705 Removed **{countryball.country}** from your wishlist.", ephemeral=True
        )

    @app_commands.command(name="purge", description="Clear your entire wishlist.")
    async def purge(self, interaction: discord.Interaction):
        items = WishlistItem.objects.filter(user_id=interaction.user.id)
        count = await items.acount()

        if count == 0:
            await interaction.response.send_message("Your wishlist is already empty.", ephemeral=True)
            return

        confirm_view = PurgeConfirmView(
            WishlistManageView(user_id=interaction.user.id),
            f"Delete all **{count}** items from your wishlist? This cannot be undone.",
        )
        await interaction.response.send_message(
            view=confirm_view,
            ephemeral=True,
        )
