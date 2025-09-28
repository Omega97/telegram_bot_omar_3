import logging
from telegram import Update
from telegram.ext import Application
from omar_bot.config.settings import BOT_TOKEN
from omar_bot.handlers.user_commands import add_user_handlers


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",  # %(name)s
    level=logging.DEBUG  # INFO
)


# Silence the httpx and telegram.ext debug messages
httpx_logger = logging.getLogger("httpx")
httpx_logger.setLevel(logging.WARNING)
telegram_logger = logging.getLogger("telegram.ext")
telegram_logger.setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def run_bot():
    """
    Builds and runs the bot application.
    """
    # Build the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers from the handlers module
    add_user_handlers(application)

    # Run the bot until the user presses Ctrl-C
    print("Bot is starting... Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
