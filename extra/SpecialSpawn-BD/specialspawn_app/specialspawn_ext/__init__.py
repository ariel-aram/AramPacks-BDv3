import logging
from typing import TYPE_CHECKING

from .cog import SpecialSpawnCog, _try_add_config_command

if TYPE_CHECKING:
    from ballsdex.core.bot import BallsDexBot

log = logging.getLogger("specialspawn")


async def setup(bot: "BallsDexBot"):
    cog = SpecialSpawnCog(bot)
    await bot.add_cog(cog)
    await cog.load_cache()

    try:
        if _try_add_config_command(bot, cog):
            log.info("Registered /config special command.")
        else:
            log.warning("Config cog not found; /config special not registered. Use /specialspawn as fallback.")
    except Exception:
        log.exception("Failed to register /config special command.")
