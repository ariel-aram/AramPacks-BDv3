import logging
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands
from discord.utils import get

from ..models import ModerationConfig, Warning

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

log = logging.getLogger("moderation_app.moderation_ext")


class Moderation(commands.Cog):
    """
    Moderation commands for managing server members.
    """

    group = app_commands.Group(name="moderation", description="Moderation commands.")

    def __init__(self, bot: "BallsDexBot"):
        self.bot = bot

    def _has_higher_role(self, guild: discord.Guild, actor: discord.Member, target: discord.Member) -> bool:
        return actor.top_role > target.top_role and guild.me.top_role > target.top_role

    @staticmethod
    def _guild_member(
        interaction: discord.Interaction["BallsDexBot"],
    ) -> tuple[discord.Guild, discord.Member]:
        assert interaction.guild is not None
        assert isinstance(interaction.user, discord.Member)
        return interaction.guild, interaction.user

    @group.command(name="kick", description="Kick a user from the server.")
    async def kick(
        self,
        interaction: discord.Interaction["BallsDexBot"],
        member: discord.Member,
        reason: str = "No reason provided.",
    ):
        guild, user = self._guild_member(interaction)
        if not user.guild_permissions.kick_members:
            return await interaction.response.send_message("You don't have permission to kick members.", ephemeral=True)

        if not self._has_higher_role(guild, user, member):
            return await interaction.response.send_message(
                "You can't kick this member due to role hierarchy.", ephemeral=True
            )

        await member.kick(reason=reason)
        await interaction.response.send_message(f"{member.mention} was kicked. Reason: {reason}")

    @group.command(name="ban", description="Ban a user from the server.")
    async def ban(
        self,
        interaction: discord.Interaction["BallsDexBot"],
        member: discord.Member,
        reason: str = "No reason provided.",
    ):
        guild, user = self._guild_member(interaction)
        if not user.guild_permissions.ban_members:
            return await interaction.response.send_message("You don't have permission to ban members.", ephemeral=True)

        if not self._has_higher_role(guild, user, member):
            return await interaction.response.send_message(
                "You can't ban this member due to role hierarchy.", ephemeral=True
            )

        await member.ban(reason=reason)
        await interaction.response.send_message(f"{member.mention} was banned. Reason: {reason}")

    @group.command(name="unban", description="Unban a user by tag (e.g. Name#1234).")
    async def unban(self, interaction: discord.Interaction["BallsDexBot"], user_tag: str):
        guild, user = self._guild_member(interaction)
        if not user.guild_permissions.ban_members:
            return await interaction.response.send_message(
                "You don't have permission to unban members.", ephemeral=True
            )

        name, discrim = user_tag.split("#")
        async for ban in guild.bans():
            if (ban.user.name, ban.user.discriminator) == (name, discrim):
                await guild.unban(ban.user)
                return await interaction.response.send_message(f"{ban.user.mention} has been unbanned.")
        await interaction.response.send_message("User not found in ban list.")

    @group.command(name="purge", description="Purge/Clear messages in the channel.")
    async def purge(self, interaction: discord.Interaction["BallsDexBot"], amount: int = 5):
        _, user = self._guild_member(interaction)
        if not user.guild_permissions.manage_messages:
            return await interaction.response.send_message(
                "You don't have permission to manage messages.", ephemeral=True
            )

        channel = interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.Thread)):
            return await interaction.response.send_message(
                "This command can only be used in text channels.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        deleted = await channel.purge(limit=amount)
        await interaction.followup.send(f"Deleted {len(deleted)} messages.", ephemeral=True)

    @group.command(name="mute", description="Mute a user.")
    async def mute(
        self,
        interaction: discord.Interaction["BallsDexBot"],
        member: discord.Member,
        reason: str = "No reason provided.",
    ):
        guild, user = self._guild_member(interaction)
        if not user.guild_permissions.manage_roles:
            return await interaction.response.send_message("You don't have permission to manage roles.", ephemeral=True)

        if not self._has_higher_role(guild, user, member):
            return await interaction.response.send_message(
                "You can't mute this member due to role hierarchy.", ephemeral=True
            )

        config, _ = await ModerationConfig.objects.aget_or_create(guild_id=guild.id)
        muted_role = None

        if config.muted_role_id:
            muted_role = guild.get_role(config.muted_role_id)

        if not muted_role:
            muted_role = get(guild.roles, name="Muted")
            if not muted_role:
                muted_role = await guild.create_role(name="Muted")
                for channel in guild.channels:
                    await channel.set_permissions(muted_role, send_messages=False, speak=False)
            config.muted_role_id = muted_role.id
            await config.asave()

        await member.add_roles(muted_role, reason=reason)
        await interaction.response.send_message(f"{member.mention} has been muted. Reason: {reason}")

    @group.command(name="unmute", description="Unmute a user.")
    async def unmute(self, interaction: discord.Interaction["BallsDexBot"], member: discord.Member):
        guild, user = self._guild_member(interaction)
        if not user.guild_permissions.manage_roles:
            return await interaction.response.send_message("You don't have permission to manage roles.", ephemeral=True)

        config = await ModerationConfig.objects.filter(guild_id=guild.id).afirst()
        muted_role = None

        if config and config.muted_role_id:
            muted_role = guild.get_role(config.muted_role_id)

        if not muted_role:
            muted_role = get(guild.roles, name="Muted")

        if muted_role and muted_role in member.roles:
            await member.remove_roles(muted_role)
            await interaction.response.send_message(f"{member.mention} has been unmuted.")
        else:
            await interaction.response.send_message("User is not muted.")

    @group.command(name="setmutedrole", description="Set the role used for muting members.")
    async def setmutedrole(self, interaction: discord.Interaction["BallsDexBot"], role: discord.Role):
        guild, user = self._guild_member(interaction)
        if not user.guild_permissions.manage_roles:
            return await interaction.response.send_message("You don't have permission to manage roles.", ephemeral=True)

        config, _ = await ModerationConfig.objects.aget_or_create(guild_id=guild.id)
        config.muted_role_id = role.id
        await config.asave()
        await interaction.response.send_message(f"Muted role set to {role.mention}.")

    @group.command(name="warn", description="Warn a user.")
    async def warn(
        self,
        interaction: discord.Interaction["BallsDexBot"],
        member: discord.Member,
        reason: str = "No reason provided.",
    ):
        guild, user = self._guild_member(interaction)
        if not user.guild_permissions.manage_messages:
            return await interaction.response.send_message("You don't have permission to warn users.", ephemeral=True)

        if not self._has_higher_role(guild, user, member):
            return await interaction.response.send_message(
                "You can't warn this member due to role hierarchy.", ephemeral=True
            )

        await Warning.objects.acreate(
            guild_id=guild.id,
            user_id=member.id,
            moderator_id=user.id,
            reason=reason,
        )
        await interaction.response.send_message(f"{member.mention} has been warned. Reason: {reason}")

    @group.command(name="warnings", description="List warnings for a user.")
    async def warnings(self, interaction: discord.Interaction["BallsDexBot"], member: discord.Member):
        guild, _ = self._guild_member(interaction)
        warns = Warning.objects.filter(guild_id=guild.id, user_id=member.id)
        if await warns.aexists():
            lines = []
            async for i, w in enumerate_warns(warns):
                lines.append(f"{i}. {w.reason} (<t:{int(w.created_at.timestamp())}:R>)")
            msg = "\n".join(lines)
            await interaction.response.send_message(f"Warnings for {member.mention}:\n{msg}")
        else:
            await interaction.response.send_message(f"{member.mention} has no warnings.")

    @group.command(name="clearwarnings", description="Clear all warnings for a user.")
    async def clearwarnings(self, interaction: discord.Interaction["BallsDexBot"], member: discord.Member):
        guild, user = self._guild_member(interaction)
        if not user.guild_permissions.manage_messages:
            return await interaction.response.send_message(
                "You don't have permission to manage warnings.", ephemeral=True
            )

        deleted_count = await Warning.objects.filter(guild_id=guild.id, user_id=member.id).adelete()
        await interaction.response.send_message(f"Cleared {deleted_count[0]} warning(s) for {member.mention}.")

    @group.command(name="slowmode", description="Set slowmode in this channel.")
    async def slowmode(self, interaction: discord.Interaction["BallsDexBot"], seconds: int):
        _, user = self._guild_member(interaction)
        if not user.guild_permissions.manage_channels:
            return await interaction.response.send_message("You don't have permission to set slowmode.", ephemeral=True)

        channel = interaction.channel
        if not isinstance(channel, discord.TextChannel):
            return await interaction.response.send_message(
                "This command can only be used in text channels.", ephemeral=True
            )

        await channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f"Slowmode set to {seconds} seconds.")

    @group.command(name="lock", description="Lock this channel.")
    async def lock(self, interaction: discord.Interaction["BallsDexBot"]):
        guild, user = self._guild_member(interaction)
        if not user.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                "You don't have permission to lock channels.", ephemeral=True
            )

        channel = interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
            return await interaction.response.send_message(
                "This command can only be used in guild channels.", ephemeral=True
            )

        overwrite = channel.overwrites_for(guild.default_role)
        overwrite.send_messages = False
        await channel.set_permissions(guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("Channel locked.")

    @group.command(name="unlock", description="Unlock this channel.")
    async def unlock(self, interaction: discord.Interaction["BallsDexBot"]):
        guild, user = self._guild_member(interaction)
        if not user.guild_permissions.manage_channels:
            return await interaction.response.send_message(
                "You don't have permission to unlock channels.", ephemeral=True
            )

        channel = interaction.channel
        if not isinstance(channel, (discord.TextChannel, discord.VoiceChannel)):
            return await interaction.response.send_message(
                "This command can only be used in guild channels.", ephemeral=True
            )

        overwrite = channel.overwrites_for(guild.default_role)
        overwrite.send_messages = True
        await channel.set_permissions(guild.default_role, overwrite=overwrite)
        await interaction.response.send_message("Channel unlocked.")

    @group.command(name="nickname", description="Change a user's nickname.")
    async def nickname(
        self,
        interaction: discord.Interaction["BallsDexBot"],
        member: discord.Member,
        nickname: str,
    ):
        guild, user = self._guild_member(interaction)
        if not user.guild_permissions.manage_nicknames:
            return await interaction.response.send_message(
                "You don't have permission to change nicknames.", ephemeral=True
            )

        if not self._has_higher_role(guild, user, member):
            return await interaction.response.send_message(
                "You can't change this member's nickname due to role hierarchy.", ephemeral=True
            )

        await member.edit(nick=nickname)
        await interaction.response.send_message(f"{member.mention}'s nickname changed to: {nickname}")


async def enumerate_warns(queryset):
    counter = 1
    async for w in queryset:
        yield counter, w
        counter += 1
