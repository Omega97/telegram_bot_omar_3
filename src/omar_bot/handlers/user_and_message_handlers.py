import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from omar_bot.command_registry import COMMAND_HANDLERS
from omar_bot.core.message_processor import process_message


# Get a logger instance for this module
logger = logging.getLogger(__name__)


# ----- Message Handlers -----


async def echo(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """
    Handles any non-command text message by delegating to the message processor.
    """
    message = update.effective_message
    raw_text = message.text
    if not message or not raw_text:
        return

    # The sender of the message may be None for messages sent to channels.
    user = message.from_user
    if not user:
        return

    logger.info(f"{user.full_name} ({user.id}): {raw_text}")

    # Compute bot's reply - delegate to pure logic layer
    reply = process_message(user_id=user.id, username=user.full_name, text=raw_text)

    if reply is not None:
        await message.reply_text(reply)
        logger.info(f"→ Bot reply: {reply}")
    else:
        logger.debug("→ No reply sent (processor returned None)")


# ----- Adding Handlers to Application -----


def add_user_handlers(application: Application):
    """
    Adds all the command handlers to the bot application.
    This method is a key part of the bot's architecture, acting as
    a registry for all the ways that the bot can respond to users.
    - CommandHandler
    - MessageHandler
    - CallbackQueryHandler: for interactive elements like inline keyboards
    - ConversationHandler: manages multi-step conversations with a user
    - Pre-checkoutQueryHandler: to implement a payment feature
    - EditedMessageHandler: triggered when a user edits a message they've already sent
    - ErrorHandler*: to catch and manage any exceptions that occur during a message's processing
    """

    # Command handlers
    for name, info in COMMAND_HANDLERS.items():
        method = info["handler"]
        application.add_handler(CommandHandler(name, method))

    # Bot's response if nothing else is triggered
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
