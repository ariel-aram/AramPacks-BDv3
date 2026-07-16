import time
from typing import TYPE_CHECKING, Optional, cast

import discord
from bd_models.models import BallInstance, Player
from discord import app_commands
from discord.ext import commands

from ..models import FlexData

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

CONFIG = {
    "mod_approval_channel_id": 0,
    "public_flex_channel": 0,
}


async def flex_autocomplete(interaction: discord.Interaction, current: str):
    try:
        player, _ = await Player.objects.aget_or_create(discord_id=interaction.user.id)
        balls = []
        async for inst in BallInstance.objects.filter(player=player).select_related("ball"):
            balls.append(inst)
    except Exception:
        return []

    current = current.lower()
    choices = []

    for inst in balls:
        ball = inst.ball
        if not ball:
            continue

        label = f"#{inst.id:0X} {ball.country} ATK:{inst.attack_bonus:+d}% HP:{inst.health_bonus:+d}%"

        if current in label.lower():
            choices.append(app_commands.Choice(name=label[:100], value=str(inst.id)))

        if len(choices) >= 25:
            break

    return choices


class FlexDecisionModal(discord.ui.Modal):
    def __init__(self, view: "FlexApprovalView", approve: bool):
        super().__init__(title="Approve Flex" if approve else "Deny Flex")
        self.view_ref = view
        self.approve = approve

        self.notes = discord.ui.TextInput(
            label="Moderator note (optional)",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=500,
        )
        self.add_item(self.notes)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        await interaction.response.defer(ephemeral=True)

        instance_id = self.view_ref.instance_id
        owner_id = self.view_ref.owner_id
        public_channel_id = self.view_ref.public_channel_id

        try:
            owner_player, _ = await Player.objects.aget_or_create(discord_id=owner_id)
            instance = await BallInstance.objects.aget(id=instance_id, player=owner_player)
        except Exception:
            self.view_ref.disable_all()
            if self.view_ref.message:
                await self.view_ref.message.edit(view=self.view_ref)
            return await interaction.followup.send("This ball no longer exists or ownership changed.", ephemeral=True)

        owner_user = interaction.client.get_user(owner_id)

        if self.approve:
            public_channel = interaction.client.get_channel(public_channel_id)
            if not public_channel or not isinstance(public_channel, discord.TextChannel):
                return await interaction.followup.send("Public flex channel not found.", ephemeral=True)

            content, file, v = await instance.prepare_for_message(cast("discord.Interaction[BallsDexBot]", interaction))

            header = f"\U0001f389 **Flex Approved!**\nOwner: <@{owner_id}>\n"
            if self.notes.value:
                header += f"\U0001f4dd Note: {self.notes.value}\n\n"

            await public_channel.send(header + content, file=file, view=v)

            if owner_user:
                try:
                    msg = f"\u2705 Your flex `#{instance.id:0X}` was approved!"  # type: ignore[attr-defined]
                    if self.notes.value:
                        msg += f"\n\U0001f4dd Moderator note: {self.notes.value}"
                    await owner_user.send(msg)
                except Exception:
                    pass

            await interaction.followup.send("\u2705 Flex approved and posted!", ephemeral=True)

        else:
            if owner_user:
                try:
                    msg = f"\u274c Your flex `#{instance.id:0X}` was denied."  # type: ignore[attr-defined]
                    if self.notes.value:
                        msg += f"\n\U0001f4dd Moderator note: {self.notes.value}"
                    await owner_user.send(msg)
                except Exception:
                    pass

            await interaction.followup.send("\u274c Flex denied.", ephemeral=True)

        self.view_ref.disable_all()
        if self.view_ref.message:
            try:
                await self.view_ref.message.edit(view=self.view_ref)
            except Exception:
                pass


class FlexApprovalView(discord.ui.View):
    def __init__(self, bot, instance_id: int, owner_id: int, public_channel_id: int):
        super().__init__(timeout=None)
        self.bot = bot
        self.instance_id = instance_id
        self.owner_id = owner_id
        self.public_channel_id = public_channel_id
        self.message: Optional[discord.Message] = None

    def disable_all(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]

    @discord.ui.button(label="\u2705 Approve", style=discord.ButtonStyle.green)
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(FlexDecisionModal(self, approve=True))

    @discord.ui.button(label="\u274c Deny", style=discord.ButtonStyle.red)
    async def deny_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.send_modal(FlexDecisionModal(self, approve=False))


class Flex(commands.Cog):
    COOLDOWN_SECONDS = 86400

    def __init__(self, bot: "BallsDexBot") -> None:
        self.bot = bot

    @app_commands.command(name="flex", description="Submit one of your balls for moderator approval.")
    @app_commands.autocomplete(ball=flex_autocomplete)
    async def flex(self, interaction: discord.Interaction, ball: str) -> None:
        await interaction.response.defer(ephemeral=True)

        uid = interaction.user.id
        now = int(time.time())

        flexdata, _ = await FlexData.objects.aget_or_create(user_id=uid)

        if now - flexdata.last_flex < self.COOLDOWN_SECONDS:
            remaining_sec = self.COOLDOWN_SECONDS - (now - flexdata.last_flex)
            remaining_hrs = remaining_sec // 3600
            await interaction.followup.send(
                f"\u23f0 Slow down! You can flex again in **{remaining_hrs}h**.", ephemeral=True
            )
            return

        try:
            instance_id = int(ball)
        except ValueError:
            await interaction.followup.send("\u274c Invalid selection.", ephemeral=True)
            return

        try:
            player, _ = await Player.objects.aget_or_create(discord_id=interaction.user.id)
            instance = await BallInstance.objects.aget(id=instance_id, player=player)
        except Exception:
            await interaction.followup.send("\u274c You don't own that ball.", ephemeral=True)
            return

        mod_channel = self.bot.get_channel(CONFIG["mod_approval_channel_id"])
        if not mod_channel or not isinstance(mod_channel, discord.TextChannel):
            await interaction.followup.send(
                "\u26a0\ufe0f Flex system not configured (missing mod channel).", ephemeral=True
            )
            return

        buffer = instance.draw_card()
        file = discord.File(buffer, "card.webp")

        emoji = ""
        if instance.ball:
            emoji_obj = interaction.client.get_emoji(instance.ball.emoji_id)
            if emoji_obj:
                emoji = f"{emoji_obj} "

        name = f"{emoji}{instance.ball.country}" if instance.ball else "Unknown"

        embed = discord.Embed(
            title="\U0001f4e4 New Flex Submission",
            description=(
                f"**From:** {interaction.user.mention}\n"
                f"**ID:** `#{instance.id:0X}`\n"  # type: ignore[attr-defined]
                f"**Name:** {name}"
            ),
            color=discord.Color.blurple(),
        )
        embed.set_image(url="attachment://card.webp")

        view = FlexApprovalView(
            bot=self.bot,
            instance_id=instance.id,  # type: ignore[attr-defined]
            owner_id=interaction.user.id,
            public_channel_id=CONFIG["public_flex_channel"],
        )
        msg = await mod_channel.send(embed=embed, file=file, view=view)
        view.message = msg

        try:
            await interaction.user.send(
                f"\U0001f4e8 Your flex `#{instance.id:0X}` has been submitted for review!"  # type: ignore[attr-defined]
            )
        except Exception:
            pass

        flexdata.last_flex = now
        await flexdata.asave()

        await interaction.followup.send("\u2705 Your flex has been submitted for moderator review!", ephemeral=True)
