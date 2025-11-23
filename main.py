r"""
Run the bot from here.

To run the user management console:
python .\scripts\user_editor_console.py

IMPORTANT: Before deploying, disable the debug mode in the ".env" file:
DEBUG=False
"""
import logging
from src.omar_bot.bot import run_bot
from omar_bot.config.settings import LOG_LEVEL


if __name__ == "__main__":
    # Configure logging using the level from .env
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=LOG_LEVEL
    )
    logging.info("Bot application starting...")
    run_bot()
