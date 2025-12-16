import logging
from telegram import Update
from telegram.ext import Application, ContextTypes
from omar_bot.config.settings import BOT_TOKEN
from omar_bot.handlers.user_commands import add_user_handlers
from omar_bot.config.settings import LOG_LEVEL


# Get a logger for this module — do NOT call basicConfig here
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=LOG_LEVEL
)


async def error_handler(_: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors. Takes as input an 'update' and a 'context'."""
    logger.error("Exception while handling an update:", exc_info=context.error)


def run_bot():
    logger.info("Bot is starting...")

    # Build the application
    application = Application.builder().token(BOT_TOKEN).build()

    # Then register admin handlers, user handlers, and echo.
    add_user_handlers(application)
    application.add_error_handler(error_handler)

    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
