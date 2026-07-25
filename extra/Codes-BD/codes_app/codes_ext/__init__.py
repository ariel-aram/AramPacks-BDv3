from typing import TYPE_CHECKING

from codes_app.codes_ext.cog import CodesCog

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot


async def setup(bot: "BallsDexBot"):
    await bot.add_cog(CodesCog(bot))
