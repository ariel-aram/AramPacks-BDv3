from __future__ import annotations

import contextlib
import time
from concurrent.futures import ThreadPoolExecutor
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
        async for inst in (
            BallInstance.objects.filter(player=player, deleted=False).select_related("ball").order_by("-id")
        ):
            balls.append(inst)
    except Exception:
        return []

    current = current.lower()
    choices = []

    for inst in balls:
        ball = inst.ball
        if not ball:
            continue

        label = f"#{inst.pk:0X} {ball.country} ATK:{inst.attack_bonus:+d}% HP:{inst.health_bonus:+d}%"

        if current in label.lower():
            choices.append(app_commands.Choice(name=label[:100], value=str(inst.pk)))

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
        guild_id = self.view_ref.guild_id

        try:
            owner_player, _ = await Player.objects.aget_or_create(discord_id=owner_id)
            instance = (
                await BallInstance.objects.select_related("ball", "special")
                .aget(id=instance_id, player=owner_player, deleted=False)
            )
        except Exception:
            self.view_ref.disable_all()
            if self.view_ref.message:
                with contextlib.suppress(Exception):
                    await self.view_ref.message.edit(view=self.view_ref)
            return await interaction.followup.send("This ball no longer exists or ownership changed.", ephemeral=True)

        owner_user = interaction.client.get_user(owner_id)
        if not owner_user:
            try:
                owner_user = await interaction.client.fetch_user(owner_id)
            except Exception:
                owner_user = None

        if self.approve:
            config = await FlexGuildConfig.objects.filter(guild_id=guild_id).afirst()
            public_channel_id = config.public_flex_channel_id if config else self.view_ref.public_channel_id
            if not public_channel_id:
                return await interaction.followup.send(
                    "Public flex channel is not configured. Use `/flexconfig public_channel` first.",
                    ephemeral=True,
                )

            public_channel = interaction.client.get_channel(public_channel_id)
            if not public_channel:
                try:
                    public_channel = await interaction.client.fetch_channel(public_channel_id)
                except Exception:
                    public_channel = None

            if not public_channel or not isinstance(public_channel, (discord.TextChannel, discord.Thread)):
                return await interaction.followup.send("Public flex channel not found or inaccessible.", ephemeral=True)

            content, file, v = await instance.prepare_for_message(cast("discord.Interaction[BallsDexBot]", interaction))

            header = f"\U0001f389 **Flex Approved!**\nOwner: <@{owner_id}>\n"
            if self.notes.value:
                header += f"\U0001f4dd Note: {self.notes.value}\n\n"

            await public_channel.send(header + content, file=file, view=v)

            if owner_user:
                try:
                    msg = f"\u2705 Your flex `#{instance.pk:0X}` was approved!"
                    if self.notes.value:
                        msg += f"\n\U0001f4dd Moderator note: {self.notes.value}"
                    await owner_user.send(msg)
                except Exception:
                    pass

            await interaction.followup.send("\u2705 Flex approved and posted!", ephemeral=True)

        else:
            if owner_user:
                try:
                    msg = f"\u274c Your flex `#{instance.pk:0X}` was denied."
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
    def __init__(
        self,
        bot: BallsDexBot,
        instance_id: int,
        owner_id: int,
        guild_id: int,
        public_channel_id: int | None = None,
    ) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.instance_id = instance_id
        self.owner_id = owner_id
        self.guild_id = guild_id
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

    @config_group.command(name="setup", description="Enable flex and configure channels.")
    @app_commands.describe(
        mod_channel="Channel where flex submissions are sent for review.",
        public_channel="Optional: Channel where approved flexes are posted publicly.",
    )
    @app_commands.guild_only()
    async def config_setup(
        self,
        interaction: discord.Interaction,
        mod_channel: discord.TextChannel,
        public_channel: discord.TextChannel | None = None,
    ) -> None:
        assert interaction.guild is not None
        config, _ = await FlexGuildConfig.objects.aget_or_create(guild_id=interaction.guild.id)
        config.mod_approval_channel_id = mod_channel.id
        if public_channel is not None:
            config.public_flex_channel_id = public_channel.id
        config.enabled = True
        await config.asave()

        pub_text = (
            f"and public flexes will be posted in <#{config.public_flex_channel_id}>."
            if config.public_flex_channel_id
            else "Use `/flexconfig public_channel` to set the public showcase channel."
        )
        await interaction.response.send_message(
            f"\u2705 Flex system enabled! Submissions will go to {mod_channel.mention} {pub_text}",
            ephemeral=True,
        )

    @config_group.command(name="public_channel", description="Set the public channel for approved flexes.")
    @app_commands.describe(channel="Channel where approved flexes are posted publicly.")
    @app_commands.guild_only()
    async def config_public_channel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        assert interaction.guild is not None
        config, _ = await FlexGuildConfig.objects.aget_or_create(guild_id=interaction.guild.id)
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
        if config is None:
            await interaction.response.send_message("Flex system is not configured for this server.", ephemeral=True)
            return

        status_str = "**enabled**" if config.enabled else "**disabled**"
        mod_ch = f"<#{config.mod_approval_channel_id}>" if config.mod_approval_channel_id else "*not set*"
        pub_ch = f"<#{config.public_flex_channel_id}>" if config.public_flex_channel_id else "*not set*"

        await interaction.response.send_message(
            f"## Flex Configuration\nStatus: {status_str}\nMod channel: {mod_ch}\nPublic channel: {pub_ch}",
            ephemeral=True,
        )

    @app_commands.command(name="flex", description="Submit one of your balls for moderator approval.")
    @app_commands.autocomplete(ball=flex_autocomplete)
    @app_commands.guild_only()
    async def flex(self, interaction: discord.Interaction, ball: str) -> None:
        await interaction.response.defer(ephemeral=True)

        assert interaction.guild is not None
        uid = interaction.user.id
        now = int(time.time())

        config = await self._get_config(interaction.guild.id)
        if config is None or not config.enabled or not config.mod_approval_channel_id:
            await interaction.followup.send(
                "\u26a0\ufe0f Flex system is not configured for this server. Ask an admin to run `/flexconfig setup`.",
                ephemeral=True,
            )
            return

        if not config.public_flex_channel_id:
            await interaction.followup.send(
                "\u26a0\ufe0f Public flex channel is not configured. Ask an admin to run `/flexconfig public_channel`.",
                ephemeral=True,
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
            instance = (
                await BallInstance.objects.select_related("ball", "special")
                .aget(id=instance_id, player=player, deleted=False)
            )
        except Exception:
            await interaction.followup.send("\u274c You don't own that ball.", ephemeral=True)
            return

        mod_channel = self.bot.get_channel(config.mod_approval_channel_id)
        if not mod_channel:
            try:
                mod_channel = await self.bot.fetch_channel(config.mod_approval_channel_id)
            except Exception:
                mod_channel = None

        if not mod_channel or not isinstance(mod_channel, (discord.TextChannel, discord.Thread)):
            await interaction.followup.send(
                "\u26a0\ufe0f Mod approval channel not found. Contact an admin.", ephemeral=True
            )
            return

        with ThreadPoolExecutor() as pool:
            buffer = await interaction.client.loop.run_in_executor(pool, instance.draw_card)
        file = discord.File(buffer, "card.webp")

        emoji = ""
        if instance.ball:
            emoji_obj = interaction.client.get_emoji(instance.ball.emoji_id)
            if emoji_obj:
                emoji = f"{emoji_obj} "

        name = f"{emoji}{instance.ball.country}" if instance.ball else "Unknown"

        embed = discord.Embed(
            title="\U0001f4e4 New Flex Submission",
            description=(f"**From:** {interaction.user.mention}\n**ID:** `#{instance.pk:0X}`\n**Name:** {name}"),
            color=discord.Color.blurple(),
        )
        embed.set_image(url="attachment://card.webp")

        view = FlexApprovalView(
            bot=self.bot,
            instance_id=instance.pk,
            owner_id=interaction.user.id,
            guild_id=interaction.guild.id,
            public_channel_id=config.public_flex_channel_id,
        )
        msg = await mod_channel.send(embed=embed, file=file, view=cast("discord.ui.View", view))
        view.message = msg

        with contextlib.suppress(Exception):
            await interaction.user.send(f"\U0001f4e8 Your flex `#{instance.pk:0X}` has been submitted for review!")

        flexdata.last_flex = now
        await flexdata.asave()

        await interaction.followup.send("\u2705 Your flex has been submitted for moderator review!", ephemeral=True)
