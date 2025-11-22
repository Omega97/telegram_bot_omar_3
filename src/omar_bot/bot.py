import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters
from omar_bot.config.settings import BOT_TOKEN
from omar_bot.handlers.user_commands import add_user_handlers
from omar_bot.config.settings import LOG_LEVEL


# Get a logger for this module — do NOT call basicConfig here
logger = logging.getLogger(__name__)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=LOG_LEVEL
)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)


def run_bot():
    logger.info("Bot is starting...")
    application = Application.builder().token(BOT_TOKEN).build()

    # Register admin command handlers FIRST
    from omar_bot.handlers.admin_commands import (
        set_canvas_command, reset_canvas_command, delete_canvas_command, canvas_confirmation_handler
    )
    application.add_handler(CommandHandler("set_canvas", set_canvas_command))
    application.add_handler(CommandHandler("reset_canvas", reset_canvas_command))
    application.add_handler(CommandHandler("delete_canvas", delete_canvas_command))
    # Add confirmation handler BEFORE the echo handler
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, canvas_confirmation_handler))

    # Then register user handlers (which includes echo)
    add_user_handlers(application)

    application.add_error_handler(error_handler)

    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
