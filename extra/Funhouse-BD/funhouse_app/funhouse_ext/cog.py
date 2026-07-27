from __future__ import annotations

import random
from typing import TYPE_CHECKING, cast

import discord
from ballsdex.core.discord import LayoutView
from discord import app_commands
from discord.ext import commands
from discord.ui import ActionRow, Container, TextDisplay

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


class RerollFortuneView(LayoutView):
    def __init__(self, share: bool):
        super().__init__(timeout=30)
        self.share = share
        self.container = RerollFortuneContainer(
            TextDisplay(self._format_fortune(random.choice(FORTUNES))),
        )
        self.add_item(self.container)

    @staticmethod
    def _format_fortune(text: str) -> str:
        return f"## \U0001f52e Your Fortune\n{text}\n\n*Take it with a grain of glitter \u2728*"

    async def on_timeout(self) -> None:  # type: ignore[override]
        for child in self.walk_children():
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


class RerollFortuneContainer(Container):
    btn_row = ActionRow()

    @btn_row.button(label="\U0001f52e Another Fortune!", style=discord.ButtonStyle.primary)
    async def reroll(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        parent = cast("RerollFortuneView", self.view)
        fortune_text = random.choice(FORTUNES)
        for child in self.walk_children():
            if isinstance(child, TextDisplay):
                child.content = parent._format_fortune(fortune_text)
        await interaction.response.edit_message(view=parent)


class CheerAgainView(LayoutView):
    def __init__(self, target: discord.User | discord.Member):
        super().__init__(timeout=30)
        self.target = target
        cheer_text = random.choice(CHEERS)
        content = f"## \U0001f4ab A Cheer Appears!\n{target.mention}, {cheer_text}\n\n*Spread the hype!*"
        self.container = CheerAgainContainer(TextDisplay(content))
        self.add_item(self.container)

    @staticmethod
    def _format_cheer(target: discord.User | discord.Member) -> str:
        cheer_text = random.choice(CHEERS)
        return f"## \U0001f4ab A Cheer Appears!\n{target.mention}, {cheer_text}\n\n*Spread the hype!*"

    async def on_timeout(self) -> None:  # type: ignore[override]
        for child in self.walk_children():
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


class CheerAgainContainer(Container):
    btn_row = ActionRow()

    @btn_row.button(label="\U0001f4a5 Cheer Again!", style=discord.ButtonStyle.primary)
    async def cheer_again(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        parent = cast("CheerAgainView", self.view)
        content = parent._format_cheer(parent.target)
        for child in self.walk_children():
            if isinstance(child, TextDisplay):
                child.content = content
        await interaction.response.edit_message(view=parent)


class ConfettiButtonView(LayoutView):
    def __init__(self):
        super().__init__(timeout=30)
        self.count = 1
        moment = random.choice(CONFETTI_MOMENTS)
        emoji = random.choice(
            ["\U0001f389", "\U0001f38a", "\u2728", "\U0001f973", "\U0001faa9", "\u2b50", "\U0001f388"]
        )
        content = f"{moment}\n{emoji * 5}\n\n*Click the button for more confetti!*"
        self.container = ConfettiButtonContainer(TextDisplay(content))
        self.add_item(self.container)

    async def on_timeout(self) -> None:  # type: ignore[override]
        for child in self.walk_children():
            if hasattr(child, "disabled"):
                child.disabled = True  # type: ignore[attr-defined]


class ConfettiButtonContainer(Container):
    btn_row = ActionRow()

    @btn_row.button(label="\U0001f389 More Confetti!", style=discord.ButtonStyle.primary)
    async def more_confetti(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        parent = cast("ConfettiButtonView", self.view)
        parent.count += 1
        moment = random.choice(CONFETTI_MOMENTS)
        emoji = random.choice(
            ["\U0001f389", "\U0001f38a", "\u2728", "\U0001f973", "\U0001faa9", "\u2b50", "\U0001f388"]
        )
        content = f"{moment}\n{emoji * min(parent.count, 10)}\n\n*Confetti storms: {parent.count}*"
        for child in self.walk_children():
            if isinstance(child, TextDisplay):
                child.content = content
        await interaction.response.edit_message(view=parent)


class Funhouse(commands.Cog):
    """Lighthearted slash commands with interactive components."""

    def __init__(self, bot: BallsDexBot) -> None:
        self.bot = bot

    @app_commands.command(name="fortune", description="Receive a playful fortune with a reroll button.")
    @app_commands.describe(share="Share publicly instead of sending ephemerally.")
    @app_commands.guild_only()
    async def fortune(self, interaction: discord.Interaction, share: bool = False) -> None:
        view = RerollFortuneView(share=share)
        await interaction.response.send_message(view=view, ephemeral=not share)

    @app_commands.command(name="cheer", description="Send an upbeat cheer with a reroll button.")
    @app_commands.describe(user="Who needs a pep talk? Leave blank for yourself.")
    @app_commands.guild_only()
    async def cheer(self, interaction: discord.Interaction, user: discord.User | None = None) -> None:
        target: discord.User | discord.Member = user or interaction.user
        view = CheerAgainView(target=target)
        await interaction.response.send_message(view=view)

    @app_commands.command(name="confetti", description="Throw a celebration into the channel. Click for more!")
    @app_commands.guild_only()
    async def confetti(self, interaction: discord.Interaction) -> None:
        view = ConfettiButtonView()
        await interaction.response.send_message(view=view)
