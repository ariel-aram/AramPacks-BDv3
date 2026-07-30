from __future__ import annotations

import contextlib
import time
from typing import TYPE_CHECKING, cast, override

import discord
from ballsdex.core.discord import LayoutView
from ballsdex.core.discord import Modal as BallsDexModal
from bd_models.models import BallInstance, Player
from discord import app_commands
from discord.ext import commands
from discord.ui import ActionRow, Container, TextInput

from ..models import FlexData, FlexGuildConfig

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


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


class FlexDecisionModal(BallsDexModal):
    def __init__(self, view: FlexApprovalView, approve: bool):
        super().__init__(title="Approve Flex" if approve else "Deny Flex")
        self.view_ref = view
        self.approve = approve

        self.notes = TextInput(
            label="Moderator note (optional)",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=500,
        )
        self.add_item(self.notes)

    @override
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
            with contextlib.suppress(Exception):
                await self.view_ref.message.edit(view=self.view_ref)


class FlexApprovalView(LayoutView):
    def __init__(self, bot: BallsDexBot, instance_id: int, owner_id: int, public_channel_id: int) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.instance_id = instance_id
        self.owner_id = owner_id
        self.public_channel_id = public_channel_id
        self.message: discord.Message | None = None
        self._cont = FlexApprovalContainer()
        self.add_item(self._cont)

    def disable_all(self) -> None:
        for child in self.walk_children():
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


class FlexApprovalContainer(Container):
    btn_row = ActionRow()

    @btn_row.button(label="\u2705 Approve", style=discord.ButtonStyle.green)
    async def approve_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        parent = self.view
        assert parent is not None and isinstance(parent, FlexApprovalView)
        await interaction.response.send_modal(FlexDecisionModal(parent, approve=True))

    @btn_row.button(label="\u274c Deny", style=discord.ButtonStyle.red)
    async def deny_btn(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        parent = self.view
        assert parent is not None and isinstance(parent, FlexApprovalView)
        await interaction.response.send_modal(FlexDecisionModal(parent, approve=False))


class Flex(commands.Cog):
    COOLDOWN_SECONDS = 86400

    def __init__(self, bot: BallsDexBot) -> None:
        self.bot = bot

    config_group = app_commands.Group(
        name="flexconfig",
        description="Configure the flex system for this server.",
        default_permissions=discord.Permissions(manage_guild=True),
    )

    async def _get_config(self, guild_id: int) -> FlexGuildConfig | None:
        try:
            return await FlexGuildConfig.objects.aget(guild_id=guild_id)
        except FlexGuildConfig.DoesNotExist:
            return None

    @config_group.command(name="setup", description="Enable flex and set the moderator approval channel.")
    @app_commands.describe(mod_channel="Channel where flex submissions are sent for review.")
    @app_commands.guild_only()
    async def config_setup(self, interaction: discord.Interaction, mod_channel: discord.TextChannel) -> None:
        assert interaction.guild is not None
        config, _ = await FlexGuildConfig.objects.aget_or_create(guild_id=interaction.guild.id)
        config.mod_approval_channel_id = mod_channel.id
        config.enabled = True
        await config.asave()
        await interaction.response.send_message(
            f"\u2705 Flex system enabled! Submissions will be sent to {mod_channel.mention}.",
            ephemeral=True,
        )

    @config_group.command(name="public_channel", description="Set the public channel for approved flexes.")
    @app_commands.describe(channel="Channel where approved flexes are posted publicly.")
    @app_commands.guild_only()
    async def config_public_channel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        assert interaction.guild is not None
        config = await self._get_config(interaction.guild.id)
        if config is None:
            await interaction.response.send_message(
                "\u26a0\ufe0f Run `/flexconfig setup` first to enable the flex system.", ephemeral=True
            )
            return
        config.public_flex_channel_id = channel.id
        await config.asave()
        await interaction.response.send_message(
            f"\u2705 Approved flexes will be posted in {channel.mention}.", ephemeral=True
        )

    @config_group.command(name="disable", description="Disable the flex system for this server.")
    @app_commands.guild_only()
    async def config_disable(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None
        config = await self._get_config(interaction.guild.id)
        if config is None:
            await interaction.response.send_message("\u26a0\ufe0f Flex system is not set up.", ephemeral=True)
            return
        config.enabled = False
        await config.asave()
        await interaction.response.send_message("\u2705 Flex system disabled.", ephemeral=True)

    @config_group.command(name="status", description="Show current flex configuration.")
    @app_commands.guild_only()
    async def config_status(self, interaction: discord.Interaction) -> None:
        assert interaction.guild is not None
        config = await self._get_config(interaction.guild.id)
        if config is None or not config.enabled:
            await interaction.response.send_message("Flex system is not configured for this server.", ephemeral=True)
            return

        mod_ch = (
            interaction.guild.get_channel(config.mod_approval_channel_id) if config.mod_approval_channel_id else None
        )
        pub_ch = interaction.guild.get_channel(config.public_flex_channel_id) if config.public_flex_channel_id else None

        await interaction.response.send_message(
            f"## Flex Configuration\n"
            f"Status: **enabled**\n"
            f"Mod channel: {mod_ch.mention if mod_ch else 'not set'}\n"
            f"Public channel: {pub_ch.mention if pub_ch else 'not set'}",
            ephemeral=True,
        )

    @app_commands.command(name="flex", description="Submit one of your balls for moderator approval.")
    @app_commands.autocomplete(ball=flex_autocomplete)
    async def flex(self, interaction: discord.Interaction, ball: str) -> None:
        await interaction.response.defer(ephemeral=True)

        assert interaction.guild is not None
        uid = interaction.user.id
        now = int(time.time())

        config = await self._get_config(interaction.guild.id)
        if config is None or not config.enabled or not config.mod_approval_channel_id:
            await interaction.followup.send(
                "\u26a0\ufe0f Flex system is not configured for this server.", ephemeral=True
            )
            return

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

        mod_channel = self.bot.get_channel(config.mod_approval_channel_id)
        if not mod_channel or not isinstance(mod_channel, discord.TextChannel):
            await interaction.followup.send(
                "\u26a0\ufe0f Mod approval channel not found. Contact an admin.", ephemeral=True
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
            public_channel_id=config.public_flex_channel_id or 0,
        )
        await mod_channel.send(embed=embed, file=file)
        msg = await mod_channel.send(view=view)
        view.message = msg

        with contextlib.suppress(Exception):
            await interaction.user.send(
                f"\U0001f4e8 Your flex `#{instance.id:0X}` has been submitted for review!"  # type: ignore[attr-defined]
            )

        flexdata.last_flex = now
        await flexdata.asave()

        await interaction.followup.send("\u2705 Your flex has been submitted for moderator review!", ephemeral=True)
