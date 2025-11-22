r"""
Run the bot from here.

To run the user management console:
python .\scripts\user_editor_console.py
"""
import logging
from src.omar_bot.bot import run_bot
# todo implement debug mode (see .env setting)


# Configure logging at the entry point
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.DEBUG
)


# Silence verbose libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram.ext").setLevel(logging.WARNING)


if __name__ == "__main__":
    # Log that the application is starting
    logging.info("Bot application starting...")
    run_bot()
