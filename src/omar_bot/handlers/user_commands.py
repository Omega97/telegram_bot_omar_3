import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters
import asyncio
from omar_bot.config.settings import USERS_DIR
from omar_bot.services.user_service import UserService


# Get a logger instance for this module
logger = logging.getLogger(__name__)


# ----------------------
#    Command Handlers
# ----------------------


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /start
    Sends a welcome message with the user's name.
    """
    user = update.effective_user
    logger.info("User %s started the bot.", user.full_name)
    name = user.full_name.split(" ")[0]
    msg = f"Hello, {name}! I am an echo bot. Type anything and I'll repeat it back to you."
    await update.message.reply_text(msg)
    logger.info("Sent a welcome message to user %s.", user.full_name)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /help
    Sends a help message
    """
    user = update.effective_user
    logger.info("User %s requested help.", user.full_name)
    help_text = (
        "**Available Commands:**\n"
        "`/start` - Greet the bot and get a welcome message.\n"
        "`/help` - Get a list of available commands and their descriptions.\n"
        "`/users` - Show the list of all users.\n"
        "`/stop` - Gracefully terminate the bot.\n"
        "`/myprofile` - Shows your profile info.\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")
    logger.info("Sent a help message to user %s.", user.full_name)


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /users
    Displays the IDs and names of all users.
    """
    user = update.effective_user
    logger.info("User %s requested the user list.", user.full_name)
    service = UserService(users_dir=USERS_DIR)
    user_ids = service.get_user_ids()
    if not user_ids:
        msg = "No users found."
    else:
        msg = f"👥 {len(user_ids)} users:\n"
        for i, uid in enumerate(user_ids):
            username = service.get(uid, 'username')
            emoji = service.get(uid, 'emoji')
            msg += f"{i:3}) `{uid}` {emoji} {username}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")
    logger.info("Sent the user list to %s.", user.full_name)


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /stop
    Gracefully stops the bot.
    """
    user = update.effective_user
    logger.info("User %s (%s) requested bot shutdown.", user.full_name, user.id)

    # Check if user is an admin
    user_service = UserService(users_dir=USERS_DIR)
    if not user_service.is_admin(user.id):
        logger.warning("Non-admin user %s (%s) attempted to stop the bot.", user.full_name, user.id)
        await update.message.reply_text("❌ Only admins can stop the bot.")
        return

    try:
        await update.message.reply_text("Bot is shutting down...")
        logger.info("Initiating bot shutdown...")

        # Stop the polling loop with a timeout
        await asyncio.wait_for(context.application.stop(), timeout=5.0)
        logger.info("Polling stopped.")

        # Fully shut down the application
        await asyncio.wait_for(context.application.shutdown(), timeout=5.0)
        logger.info("Application fully shut down.")

        # Ensure the event loop is closed
        loop = asyncio.get_running_loop()
        loop.stop()
        logger.info("Event loop stopped.")
    except asyncio.TimeoutError:
        logger.error("Shutdown timed out, forcing termination.")
        await update.message.reply_text("⚠️ Shutdown timed out, forcing termination.")
        loop = asyncio.get_running_loop()
        loop.stop()
        loop.close()
    except Exception as e:
        logger.error("Failed to stop the bot: %s", str(e))
        await update.message.reply_text(f"❌ Error stopping the bot: {str(e)}")


async def myprofile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /myprofile
    Shows the user's profile information.
    """
    user = update.effective_user
    logger.info("User %s requested their profile.", user.full_name)
    service = UserService(users_dir=USERS_DIR)
    user_data = service.get_user(user.id)

    if not user_data:
        await update.message.reply_text("❌ You are not registered. Use /start to join!")
        return

    msg = f"👤 Your Profile:\n"
    msg += f"ID: `{user.id}`\n"
    msg += f"Username: {user_data['username']}\n"
    msg += f"Emoji: {user_data['emoji']}\n"
    msg += f"Gems: {user_data['gems']}\n"
    msg += f"Tiles Placed: {user_data['tiles_count']}\n"
    msg += f"Admin: {'Yes' if user_data['admin'] else 'No'}\n"
    msg += f"Santa: {'Yes' if user_data['santa'] else 'No'}\n"
    msg += f"Canvas: {user_data['canvas']}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")
    logger.info("Sent profile to %s.", user.full_name)


# ----------------------
#    Message Handlers
# ----------------------


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Echoes the user's message back to them.
    """
    user = update.effective_user
    logger.info(f"{user.full_name}: {update.message.text}")
    reply = update.message.text
    await update.message.reply_text(reply)
    logger.info(reply)


# ------------------------------------
#    Adding Handlers to Application
# ------------------------------------

COMMAND_HANDLERS = {"start": start,
                    "help": help_command,
                    "users": users_command,
                    "stop": stop_command,
                    "myprofile": myprofile_command
                    }


def add_user_handlers(application: Application) -> None:
    """
    Adds all user command handlers to the bot application.
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

    # command handlers
    for name, method in COMMAND_HANDLERS.items():
        application.add_handler(CommandHandler(name, method))

    # todo replace with actual bot response
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
