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
from omar_bot.config.settings import LOG_LEVEL


if __name__ == "__main__":
    # Configure logging using the level from .env
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=LOG_LEVEL
    )
    logging.info("Bot application starting...")
    env_sanity_check()
    run_bot()
