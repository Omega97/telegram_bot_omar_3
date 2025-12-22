r"""
--- To run the bot ---
python .\main.py

--- To run the user management console ---
python .\scripts\user_editor_console.py

--- IMPORTANT Before deploying Before deploying ---
- make sure to set the proper environment variables in the ".env" file
- disable the debug mode in the ".env" file (DEBUG=False)
"""
import logging
from src.omar_bot.bot import run_bot
from src.omar_bot.utils.utils import env_sanity_check
from src.omar_bot.config.settings import LOG_LEVEL
from src.omar_bot.command_registry import COMMAND_HANDLERS


# Configure logging using the level from .env, and get a logger instance for this module
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=LOG_LEVEL
)
logger = logging.getLogger(__name__)


# HIDE POLLING LOGS - Only show warnings or errors from the networking libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def main():
    logger.info("Bot application starting...")
    logging.info(f"{len(COMMAND_HANDLERS)} commands loaded")
    env_sanity_check()
    run_bot()


if __name__ == "__main__":
    main()
