from typing import TYPE_CHECKING, Optional

import discord
from bd_models.models import BallInstance, Player, balls, specials
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


async def ball_autocomplete(interaction: discord.Interaction, current: str):
    matching_balls = [b for b in balls.values() if b.enabled and current.lower() in b.country.lower()]
    return [app_commands.Choice(name=ball.country, value=str(ball.id)) for ball in matching_balls[:25]]  # type: ignore[attr-defined]


async def special_autocomplete(interaction: discord.Interaction, current: str):
    matching_specials = [s for s in specials.values() if current.lower() in s.name.lower()]
    return [app_commands.Choice(name=special.name, value=str(special.id)) for special in matching_specials[:25]]  # type: ignore[attr-defined]


class PreviewVariantsView(discord.ui.View):
    def __init__(self, ball_id: int, base_special_id: Optional[int]):
        super().__init__(timeout=60)
        self.ball_id = ball_id
        self.base_special_id = base_special_id
        self.current_special_id = base_special_id

        options = [discord.SelectOption(label="Default (no special)", value="none")]
        for s in list(specials.values())[:24]:
            options.append(
                discord.SelectOption(
                    label=s.name[:100],
                    value=str(s.id),  # type: ignore[attr-defined]
                    description=f"Rarity: {s.rarity * 100:.1f}%",
                )
            )

        self.special_select = discord.ui.Select(
            placeholder="Try a different special variant...",
            options=options,
            row=0,
        )
        self.special_select.callback = self._on_special_select
        self.add_item(self.special_select)

    async def _build_preview(self, interaction: discord.Interaction) -> tuple[discord.Embed, Optional[discord.File]]:
        selected_ball = balls.get(self.ball_id)
        if not selected_ball:
            return (
                discord.Embed(title="\u274c Error", description="Ball no longer exists.", color=discord.Color.red()),
                None,
            )

        selected_special = None
        if self.current_special_id is not None:
            selected_special = specials.get(self.current_special_id)

        player, _ = await Player.objects.aget_or_create(discord_id=interaction.user.id)
        ownership_query = BallInstance.objects.filter(player=player, ball=selected_ball)
        if selected_special:
            ownership_query = ownership_query.filter(special=selected_special)
        owned_count = await ownership_query.acount()
        ownership_text = f"You own {owned_count}" if owned_count > 0 else "Not owned"

        temp_instance = BallInstance(
            ball=selected_ball,
            special=selected_special,
            health_bonus=0,
            attack_bonus=0,
            favorite=False,
            tradeable=True,
            locked=None,
            extra_data={},
        )

        try:
            buffer = temp_instance.draw_card()
            file = discord.File(buffer, "preview_card.webp")
        except Exception:
            return (
                discord.Embed(
                    title="\u274c Preview Failed",
                    description="This special may not have artwork yet.",
                    color=discord.Color.red(),
                ),
                None,
            )

        embed = discord.Embed(
            title=f"Preview: {selected_ball.country}",
            description=f"Special: {selected_special.name if selected_special else 'Default'}",
            color=discord.Color.blue(),
        )
        embed.set_image(url="attachment://preview_card.webp")
        embed.add_field(name="Ownership", value=ownership_text, inline=True)
        embed.add_field(name="Rarity", value=f"{selected_ball.rarity}%", inline=True)

        return embed, file

    async def _on_special_select(self, interaction: discord.Interaction) -> None:
        value = self.special_select.values[0]
        if value == "none":
            self.current_special_id = None
        else:
            self.current_special_id = int(value)

        embed, file = await self._build_preview(interaction)
        kwargs = {"embed": embed, "view": self}
        if file:
            kwargs["attachments"] = [file]
        else:
            kwargs["attachments"] = []
        await interaction.response.edit_message(**kwargs)

    async def on_timeout(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


class Preview(commands.Cog):
    """Preview card images with interactive special variant switching."""

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot

    @app_commands.command(name="preview", description="Preview a card image with interactive special variants.")
    @app_commands.autocomplete(ball=ball_autocomplete, special=special_autocomplete)
    async def preview(self, interaction: discord.Interaction, ball: str, special: Optional[str] = None):
        await interaction.response.defer(ephemeral=False)

        try:
            ball_id = int(ball)
            selected_ball = balls.get(ball_id)
            if not selected_ball:
                await interaction.followup.send("Ball not found.", ephemeral=True)
                return
        except ValueError:
            await interaction.followup.send("Invalid ball selection.", ephemeral=True)
            return

        base_special_id: Optional[int] = None
        if special:
            try:
                special_id = int(special)
                selected_special = specials.get(special_id)
                if not selected_special:
                    await interaction.followup.send("Special not found.", ephemeral=True)
                    return
                base_special_id = special_id
            except ValueError:
                await interaction.followup.send("Invalid special selection.", ephemeral=True)
                return

        view = PreviewVariantsView(ball_id=ball_id, base_special_id=base_special_id)
        embed, file = await view._build_preview(interaction)

        kwargs = {"embed": embed, "view": view}
        if file:
            kwargs["file"] = file
        await interaction.followup.send(**kwargs, ephemeral=False)
