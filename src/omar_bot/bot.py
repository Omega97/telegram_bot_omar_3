import logging
import telegram
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, ExtBot, MessageHandler, filters
from src.omar_bot.config.settings import BOT_TOKEN
from src.omar_bot.handlers.user_commands import unknown_command, sticker_reply_handler
from src.omar_bot.handlers.user_and_message_handlers import add_command_handlers


# Get a logger for this module — do NOT call basicConfig here
logger = logging.getLogger(__name__)


async def error_handler(_: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors. Takes as input an 'update' and a 'context'."""
    logger.error("Exception while handling an update:", exc_info=context.error)


async def log_incoming(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Logs details of every incoming message."""
    user = update.effective_user
    msg = update.effective_message
    if msg and user:
        text = msg.text or "[Non-text content]"
        logging.info(f"INCOMING | User: {user.id} (@{user.username}) | Text: {text}")


class LoggingBot(ExtBot):
    """A custom Bot class that logs all outgoing messages."""
    async def send_message(self, chat_id, text, *args, **kwargs):
        logging.info(f"OUTGOING | To: {chat_id} | Text: \n{text}")
        return await super().send_message(chat_id, text, *args, **kwargs)


def run_bot():
    logger.info("Bot is starting...")

    # Manually create an instance of the custom LoggingBot
    custom_bot = LoggingBot(token=BOT_TOKEN)

    # Build the application by passing the bot instance directly
    application = (
        ApplicationBuilder()
        .bot(custom_bot)
        .build()
    )

    # Add the incoming logger in group -1 (it runs before commands)
    application.add_handler(MessageHandler(filters.ALL, log_incoming), group=-1)

    # Add user and admin handlers
    add_command_handlers(application)

    # This will catch any sticker sent to the bot
    application.add_handler(MessageHandler(filters.Sticker.ALL, sticker_reply_handler))

    # Unknown command handler
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))

    # application.run_polling() blocks until application.stop_running() is called
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)

        # Code execution reaches here after shutdown is triggered
        logger.info("Bot has been shut down successfully.")
    except telegram.error.TimedOut:
        logger.info("Timed out - unable to connect to remote server.")
