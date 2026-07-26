from __future__ import annotations

from typing import TYPE_CHECKING

from cardstudio_app.cardstudio_ext.cog import CardStudio

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


async def setup(bot: BallsDexBot):
    await bot.add_cog(CardStudio(bot))
