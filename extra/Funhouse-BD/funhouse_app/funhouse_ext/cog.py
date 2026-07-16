import random
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

FORTUNES = [
    "Luck is on your side\u2014just do not try to catch it with chopsticks!",
    "A shiny pull is in your future. Maybe even today. \U0001f440",
    "Your next trade will be legendary. Or hilarious. Possibly both.",
    'Beware of people offering "free" snacks. They probably want your best ball.',
    "Your luck stat just rolled a natural 20!",
    "Someone nearby is about to ping you with good news.",
    "Collect shinies, but do not forget to collect moments too.",
    "A mysterious traveler will appear with an irresistible offer.",
    "Your favorite ball is secretly cheering you on right now.",
]

CHEERS = [
    "You are absolutely crushing it today!",
    "Keep rolling\u2014your streak is not over yet!",
    "If hype were a stat, you would be max level.",
    "You make the lobby brighter just by showing up.",
    "Confidence check: you passed with flying colors!",
    "Your energy is contagious. Thanks for sharing it!",
    "No crits against you today. Promise.",
]

CONFETTI_MOMENTS = [
    "\U0001f38a A wild celebration appears!",
    "\U0001f389 Confetti cannons primed and ready!",
    "\u2728 Sparkles acquired. Deploying now...",
    "\U0001f973 The party has entered the chat!",
    "\U0001faa9 Mirrorball mode: ON",
]

COLORS = [
    discord.Color.blurple(),
    discord.Color.gold(),
    discord.Color.green(),
    discord.Color.magenta(),
    discord.Color.orange(),
]


class RerollFortuneView(discord.ui.View):
    def __init__(self, share: bool):
        super().__init__(timeout=30)
        self.share = share

    @discord.ui.button(label="\U0001f52e Another Fortune!", style=discord.ButtonStyle.primary)
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        fortune_text = random.choice(FORTUNES)
        embed = discord.Embed(
            title="\U0001f52e Your Fortune",
            description=fortune_text,
            color=random.choice(COLORS),
        )
        embed.set_footer(text="Take it with a grain of glitter \u2728")
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


class CheerAgainView(discord.ui.View):
    def __init__(self, target: discord.User | discord.Member):
        super().__init__(timeout=30)
        self.target = target

    @discord.ui.button(label="\U0001f4a5 Cheer Again!", style=discord.ButtonStyle.primary)
    async def cheer_again(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        cheer_text = random.choice(CHEERS)
        embed = discord.Embed(
            title="\U0001f4ab A Cheer Appears!",
            description=f"{self.target.mention}, {cheer_text}",
            color=random.choice(COLORS),
        )
        embed.set_thumbnail(url=getattr(self.target.display_avatar, "url", None))
        embed.set_footer(text="Spread the hype!")
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


class ConfettiButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=30)
        self.count = 1

    @discord.ui.button(label="\U0001f389 More Confetti!", style=discord.ButtonStyle.primary)
    async def more_confetti(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.count += 1
        moment = random.choice(CONFETTI_MOMENTS)
        emoji = random.choice(
            ["\U0001f389", "\U0001f38a", "\u2728", "\U0001f973", "\U0001faa9", "\u2b50", "\U0001f388"]
        )
        embed = discord.Embed(
            description=f"{moment}\n{emoji * min(self.count, 10)}",
            color=random.choice(COLORS),
        )
        embed.set_footer(text=f"Confetti storms: {self.count}")
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self) -> None:
        for child in self.children:
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


class Funhouse(commands.Cog):
    """Lighthearted slash commands with interactive components."""

    def __init__(self, bot: "BallsDexBot") -> None:
        self.bot = bot

    @app_commands.command(name="fortune", description="Receive a playful fortune with a reroll button.")
    @app_commands.describe(share="Share publicly instead of sending ephemerally.")
    @app_commands.guild_only()
    async def fortune(self, interaction: discord.Interaction, share: bool = False) -> None:
        fortune_text = random.choice(FORTUNES)
        embed = discord.Embed(
            title="\U0001f52e Your Fortune",
            description=fortune_text,
            color=random.choice(COLORS),
        )
        embed.set_footer(text="Take it with a grain of glitter \u2728")

        view = RerollFortuneView(share=share)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=not share)

    @app_commands.command(name="cheer", description="Send an upbeat cheer with a reroll button.")
    @app_commands.describe(user="Who needs a pep talk? Leave blank for yourself.")
    @app_commands.guild_only()
    async def cheer(self, interaction: discord.Interaction, user: discord.User | None = None) -> None:
        target: discord.User | discord.Member = user or interaction.user
        cheer_text = random.choice(CHEERS)
        embed = discord.Embed(
            title="\U0001f4ab A Cheer Appears!",
            description=f"{target.mention}, {cheer_text}",
            color=random.choice(COLORS),
        )
        embed.set_thumbnail(url=getattr(target.display_avatar, "url", None))
        embed.set_footer(text="Spread the hype!")

        view = CheerAgainView(target=target)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="confetti", description="Throw a celebration into the channel. Click for more!")
    @app_commands.guild_only()
    async def confetti(self, interaction: discord.Interaction) -> None:
        moment = random.choice(CONFETTI_MOMENTS)
        emoji = random.choice(
            ["\U0001f389", "\U0001f38a", "\u2728", "\U0001f973", "\U0001faa9", "\u2b50", "\U0001f388"]
        )
        embed = discord.Embed(
            description=f"{moment}\n{emoji * 5}",
            color=random.choice(COLORS),
        )
        embed.set_footer(text="Click the button for more confetti!")

        view = ConfettiButtonView()
        await interaction.response.send_message(embed=embed, view=view)
