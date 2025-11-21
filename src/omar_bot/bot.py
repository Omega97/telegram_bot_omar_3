import logging
from telegram import Update
from telegram.ext import Application
from omar_bot.config.settings import BOT_TOKEN
from omar_bot.handlers.user_commands import add_user_handlers


# Get a logger for this module — do NOT call basicConfig here
logger = logging.getLogger(__name__)


def run_bot():
    """
    Builds and runs the bot application.
    """
    logger.info("Bot is starting...")

    # Build the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Register handlers
    add_user_handlers(application)

    # Run the bot until the user presses Ctrl-C
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
