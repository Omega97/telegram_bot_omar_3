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
import sys
from omar_bot.bot import run_bot
from omar_bot.utils.utils import env_sanity_check
from omar_bot.config.settings import LOG_LEVEL
from omar_bot.command_registry import setup_commands


BLUE = "\033[94m"
GREEN = "\033[92m"
RESET = "\033[0m"


class ColoredFormatter(logging.Formatter):
    """Colorizes INCOMING (blue) and OUTGOING (green) log lines."""

    def __init__(self, fmt=None, datefmt=None, style="%", use_colors=True):
        super().__init__(fmt, datefmt, style)
        self.use_colors = use_colors

    def format(self, record):
        formatted = super().format(record)
        if not self.use_colors:
            return formatted

        message = record.getMessage()
        if message.startswith("INCOMING"):
            return f"{BLUE}{formatted}{RESET}"
        if message.startswith("OUTGOING"):
            return f"{GREEN}{formatted}{RESET}"
        return formatted


def configure_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(
        ColoredFormatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            use_colors=sys.stdout.isatty(),
        )
    )
    logging.basicConfig(level=LOG_LEVEL, handlers=[handler])


# Configure logging using the level from .env, and get a logger instance for this module
configure_logging()
logger = logging.getLogger(__name__)


# HIDE POLLING LOGS - Only show warnings or errors from the networking libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


def main():
    logger.info("Bot application starting...")
    commands = setup_commands()
    logging.info(f"✅ {len(commands)} commands loaded")
    env_sanity_check()
    run_bot()


if __name__ == "__main__":
    main()
