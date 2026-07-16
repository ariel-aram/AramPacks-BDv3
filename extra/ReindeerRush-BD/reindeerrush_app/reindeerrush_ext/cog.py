import asyncio
import random
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

REINDEER_DATA = [
    {"name": "Dasher", "emoji": "\U0001f98c", "color": 0xE74C3C},
    {"name": "Prancer", "emoji": "\U0001f98c", "color": 0x2ECC71},
    {"name": "Vixen", "emoji": "\U0001f98c", "color": 0x3498DB},
    {"name": "Comet", "emoji": "\U0001f98c", "color": 0x9B59B6},
    {"name": "Rudolph", "emoji": "\U0001f534", "color": 0xF1C40F},
]

FINISH_EMOJI = "\U0001f3c1"
TRACK_TILE = "\U0001f7e9"
EMPTY_TILE = "\u2b1c"
TRACK_LENGTH = 15
TICK_SPEED = 0.8


class ReindeerRaceView(discord.ui.View):
    def __init__(self, host: discord.User | discord.Member):
        super().__init__(timeout=60)
        self.host_id = host.id
        self.started = False
        self.rooters: dict[str, list[int]] = {r["name"]: [] for r in REINDEER_DATA}

        options = [
            discord.SelectOption(label=r["name"], emoji=r["emoji"], description=f"Root for {r['name']}!")
            for r in REINDEER_DATA
        ]
        self.select_reindeer = discord.ui.Select(
            placeholder="Pick a reindeer to root for!",
            options=options,
        )
        self.select_reindeer.callback = self._on_select
        self.add_item(self.select_reindeer)

    async def _on_select(self, interaction: discord.Interaction) -> None:
        if self.started:
            await interaction.response.send_message("The race has already started!", ephemeral=True)
            return
        chosen = self.select_reindeer.values[0]
        for name, users in self.rooters.items():
            if interaction.user.id in users:
                users.remove(interaction.user.id)
        self.rooters[chosen].append(interaction.user.id)
        await interaction.response.send_message(f"You're rooting for **{chosen}**! \U0001f3c6", ephemeral=True)

    @discord.ui.button(label="\U0001f3c1 Start Race!", style=discord.ButtonStyle.green)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if interaction.user.id != self.host_id:
            await interaction.response.send_message("Only the race host can start the race!", ephemeral=True)
            return
        if self.started:
            await interaction.response.send_message("The race is already running!", ephemeral=True)
            return
        self.started = True
        await interaction.response.defer()
        await self._run_race(interaction)

    async def _draw_track(self, positions: dict[str, int]) -> str:
        lines: list[str] = []
        for reindeer in REINDEER_DATA:
            name = reindeer["name"]
            pos = positions[name]
            filled = TRACK_TILE * min(pos, TRACK_LENGTH)
            empty = EMPTY_TILE * max(0, TRACK_LENGTH - pos)
            lines.append(f"{reindeer['emoji']}  {filled}{empty}  {FINISH_EMOJI}")
        return "\n".join(lines)

    async def _run_race(self, interaction: discord.Interaction) -> None:
        reindeer_names = [r["name"] for r in REINDEER_DATA]
        positions: dict[str, int] = {name: 0 for name in reindeer_names}
        finished: list[str] = []

        message = interaction.message
        if message is None:
            return

        embed = discord.Embed(
            title="\U0001f3c6 Reindeer Rush \U0001f3c6",
            description="The race has begun!",
            color=0xE74C3C,
        )

        for _ in range(50):
            for name in reindeer_names:
                if name in finished:
                    continue
                advance = random.choices([1, 2, 3], weights=[3, 3, 1], k=1)[0]
                positions[name] = min(positions[name] + advance, TRACK_LENGTH)
                if positions[name] >= TRACK_LENGTH and name not in finished:
                    finished.append(name)

            track = await self._draw_track(positions)
            embed.description = f"{track}\n\n"
            if finished:
                winner = finished[0]
                reindeer_info = next(r for r in REINDEER_DATA if r["name"] == winner)
                rooters = self.rooters[winner]
                if rooters:
                    mentions = ", ".join(f"<@{uid}>" for uid in rooters[:10])
                    embed.description += f"\U0001f389 **{reindeer_info['emoji']} {winner} wins!**\n"
                    embed.description += f"Rooters: {mentions}"
                else:
                    embed.description += f"\U0001f389 **{reindeer_info['emoji']} {winner} wins!**"
                embed.color = reindeer_info["color"]
            else:
                leader = max(positions, key=lambda n: positions[n])
                reindeer_info = next(r for r in REINDEER_DATA if r["name"] == leader)
                embed.description += f"In the lead: {reindeer_info['emoji']} **{leader}**"
                embed.color = reindeer_info["color"]

            self.clear_items()
            await message.edit(embed=embed, view=self)
            if finished:
                break

            await asyncio.sleep(TICK_SPEED)

        self.stop()

    async def on_timeout(self) -> None:
        if not self.started:
            self.clear_items()
            self.add_item(
                discord.ui.Button(
                    label="Race expired",
                    style=discord.ButtonStyle.secondary,
                    disabled=True,
                )
            )


class ReindeerRush(commands.Cog):
    """A festive reindeer racing game with interactive components."""

    def __init__(self, bot: "BallsDexBot") -> None:
        self.bot = bot

    @app_commands.command(
        name="reindeerrush", description="Start a reindeer race! Pick your reindeer and root for them!"
    )
    @app_commands.guild_only()
    async def reindeerrush(self, interaction: discord.Interaction) -> None:
        view = ReindeerRaceView(host=interaction.user)

        reindeer_lines = [f"{r['emoji']} **{r['name']}**" for r in REINDEER_DATA]
        embed = discord.Embed(
            title="\U0001f98c Reindeer Rush \U0001f3c1",
            description=(
                "A reindeer race is about to begin!\n\n"
                + " | ".join(reindeer_lines)
                + "\n\nUse the dropdown below to pick your reindeer, then press **Start Race**!"
            ),
            color=0xE74C3C,
        )
        embed.set_footer(text=f"Hosted by {interaction.user.display_name}")

        await interaction.response.send_message(embed=embed, view=view)
