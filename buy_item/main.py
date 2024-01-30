import asyncio
from buy_module.buy_order_bot import SteamBot
from buy_module.server_get_request import run_server
from buy_module.utils import logger
import os
from dotenv import load_dotenv

load_dotenv()


async def interrupt_handler(steam_bot_):
    logger.info("Interrupt signal received. Stopping the loops and saving data.")
    steam_bot_.cleanup()
    logger.info("Steam client logout.")


if __name__ == "__main__":
    config_file = os.getenv("PATH_TO_CONFIG")
    steam_guard_file = os.getenv("PATH_TO_STEAM_GUARD")

    steam_bot = SteamBot(config_file=config_file, steam_guard_file=steam_guard_file)
    steam_bot.main()

    # signal.signal(signal.SIGINT, signal_handler)

    try:
        asyncio.run(run_server(steam_bot))
    except asyncio.CancelledError:
        logger.info("Server stopped.")
    finally:
        steam_bot.cleanup()
        logger.info("Application shutdown completed.")
