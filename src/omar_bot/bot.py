import logging
import telegram
from telegram import Update
from telegram.ext import Application, ContextTypes
from omar_bot.config.settings import BOT_TOKEN
from omar_bot.handlers.user_and_message_handlers import add_user_handlers


# Get a logger for this module — do NOT call basicConfig here
logger = logging.getLogger(__name__)


async def error_handler(_: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors. Takes as input an 'update' and a 'context'."""
    logger.error("Exception while handling an update:", exc_info=context.error)


def run_bot():
    logger.info("Bot is starting...")
    application = Application.builder().token(BOT_TOKEN).build()

    add_user_handlers(application)
    application.add_error_handler(error_handler)

    # application.run_polling() blocks until application.stop_running() is called
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)

        # Code execution reaches here after shutdown is triggered
        logger.info("Bot has been shut down successfully.")
    except telegram.error.TimedOut:
        logger.info("Timed out - unable to connect to remote server.")
