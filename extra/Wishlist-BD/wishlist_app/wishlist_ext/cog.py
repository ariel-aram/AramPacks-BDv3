import discord
from ballsdex.core.utils.transformers import BallTransformer
from bd_models.models import Ball, BallInstance
from discord import app_commands
from discord.ext import commands
from django.core.exceptions import ObjectDoesNotExist

from ..models import WishlistItem


class WishlistManageView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=60)
        self.user_id = user_id

    async def _get_wishlist_data(self) -> list[dict[str, str]]:
        items = [item async for item in WishlistItem.objects.filter(user_id=self.user_id)]
        result = []
        for item in items:
            ball = await Ball.objects.filter(country__iexact=item.ball_country).afirst()
            owned = (
                await BallInstance.objects.filter(player__discord_id=self.user_id, ball=ball).acount() if ball else 0
            )
            result.append(
                {
                    "country": ball.country if ball else item.ball_country,
                    "owned": str(owned),
                }
            )
        return result

    async def _build_embed(self) -> discord.Embed:
        data = await self._get_wishlist_data()
        if not data:
            embed = discord.Embed(
                title="\U0001f381 Wishlist",
                description="Your wishlist is empty.",
                color=discord.Color.gold(),
            )
            return embed

        lines = []
        for item in data:
            lines.append(f"{item['country']} ({item['owned']} owned)")

        embed = discord.Embed(
            title="\U0001f381 Your Wishlist",
            description="\n".join(lines),
            color=discord.Color.gold(),
        )
        embed.set_footer(text=f"{len(data)} item(s) on your wishlist")
        return embed

    @discord.ui.select(placeholder="\u2795 Manage wishlist...")
    async def manage_select(self, interaction: discord.Interaction, select: discord.ui.Select) -> None:
        return

    async def _refresh_select(self) -> discord.Embed:
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
        self.manage_select.options = options
        return await self._build_embed()

    @discord.ui.button(label="\U0001f5d1\ufe0f Remove Selected", style=discord.ButtonStyle.danger, row=1)
    async def remove_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        values = self.manage_select.values
        if not values or values[0] == "_none":
            await interaction.response.send_message("Select an item to remove first.", ephemeral=True)
            return

        country = values[0]
        try:
            item = await WishlistItem.objects.aget(user_id=self.user_id, ball_country=country)
            await item.adelete()
        except ObjectDoesNotExist:
            await interaction.response.send_message("Item not found in your wishlist.", ephemeral=True)
            return

        embed = await self._refresh_select()
        embed.set_footer(text=f"\u2705 Removed {country} from your wishlist")
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="\u274c Purge All", style=discord.ButtonStyle.secondary, row=1)
    async def purge_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        items = WishlistItem.objects.filter(user_id=self.user_id)
        count = await items.acount()
        if count == 0:
            await interaction.response.send_message("Your wishlist is already empty.", ephemeral=True)
            return

        confirm_view = PurgeConfirmView(self)
        await interaction.response.send_message(
            f"Delete all **{count}** items from your wishlist?",
            view=confirm_view,
            ephemeral=True,
        )

    async def on_timeout(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


class PurgeConfirmView(discord.ui.View):
    def __init__(self, parent: WishlistManageView):
        super().__init__(timeout=15)
        self.parent = parent

    @discord.ui.button(label="\u2705 Yes, Purge All", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        items = WishlistItem.objects.filter(user_id=self.parent.user_id)
        await items.adelete()
        await interaction.response.edit_message(content="\u2705 Wishlist cleared.", view=None)

    @discord.ui.button(label="\u274c Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(content="Purge cancelled.", view=None)


@app_commands.guild_only()
class Wishlist(commands.GroupCog, group_name="wishlist"):
    def __init__(self, bot):
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
            embed = discord.Embed(
                title=f"{target.display_name}'s Wishlist",
                description="\n".join(lines),
                color=discord.Color.gold(),
            )
            await interaction.response.send_message(embed=embed)
            return

        view = WishlistManageView(user_id=interaction.user.id)
        embed = await view._refresh_select()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

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

        confirm_view = PurgeConfirmView(WishlistManageView(user_id=interaction.user.id))
        await interaction.response.send_message(
            f"Delete all **{count}** items from your wishlist? This cannot be undone.",
            view=confirm_view,
            ephemeral=True,
        )
