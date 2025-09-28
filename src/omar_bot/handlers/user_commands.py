import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters
import asyncio
from omar_bot.config.settings import USERS_DIR
from omar_bot.services.user_service import UserService
from omar_bot.services.santa import SantaService


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
        "`/users` - Show the list of all users by nickname.\n"
        "`/gems` - Show the list of all users with their gems.\n"
        "`/gold` - Show the list of all users with their gold.\n"
        "`/stop` - Gracefully terminate the bot (admin-only).\n"
        "`/myprofile` - Shows your profile info.\n"
        "`/santa` - Manage Secret Santa participation and assignments.\n"
        "  - `/santa join` - Join the Secret Santa event.\n"
        "  - `/santa who` - See your assigned giftee and participants.\n"
        "  - `/santa status` - Check your participation status and participants.\n"
        "  - `/santa assign` - Assign Secret Santa pairs (admin-only).\n"
        "  - `/santa reset` - Reset the Secret Santa event (admin-only).\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")
    logger.info("Sent a help message to user %s.", user.full_name)


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /users
    Displays the IDs, emojis, and nicknames of all users.
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
            user_data = service.get_user(uid)
            nickname = user_data.get('nickname', user_data.get('username', 'Unknown'))
            emoji = user_data.get('emoji', '')
            msg += f"{emoji} {nickname}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")
    logger.info("Sent the user list to %s.", user.full_name)


async def gems_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /gems
    Displays the IDs, emojis, nicknames, and gems of all users.
    """
    user = update.effective_user
    logger.info("User %s requested the gems list.", user.full_name)
    service = UserService(users_dir=USERS_DIR)
    user_ids = service.get_user_ids()
    user_ids = [uid for uid in user_ids if service.get_user(uid).get('gems', 0)]

    if not user_ids:
        msg = "No users found."
    else:
        msg = f"💎 {len(user_ids)} users with gems:\n"
        for i, uid in enumerate(user_ids):
            user_data = service.get_user(uid)
            nickname = user_data.get('nickname', user_data.get('username', 'Unknown'))
            emoji = user_data.get('emoji', '')
            gems = user_data.get('gems', 0)
            line = f"{emoji} {nickname}:  {gems}"
            # line = line.replace(" ", "_")
            msg += f"{line}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")
    logger.info("Sent the gems list to %s.", user.full_name)


async def gold_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /gold
    Displays the IDs, emojis, nicknames, and gold of all users.
    """
    user = update.effective_user
    logger.info("User %s requested the gold list.", user.full_name)
    service = UserService(users_dir=USERS_DIR)
    user_ids = service.get_user_ids()
    user_ids = [uid for uid in user_ids if service.get_user(uid).get('gold', 0)]

    if not user_ids:
        msg = "No users found."
    else:
        msg = f"🟡 {len(user_ids)} users with gold:\n"
        for i, uid in enumerate(user_ids):
            user_data = service.get_user(uid)
            nickname = user_data.get('nickname', user_data.get('username', 'Unknown'))
            emoji = user_data.get('emoji', '')
            gold = user_data.get('gold', 0)
            if gold:
                line = f"{emoji} {nickname}:  {gold}"
                # line = line.replace(" ", "_")
                msg += f"{line}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")
    logger.info("Sent the gold list to %s.", user.full_name)


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

        # Log active tasks
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        logger.debug("Active tasks before shutdown: %s", [t.get_name() for t in tasks])

        # Stop the polling loop
        logger.debug("Calling application.stop()...")
        await asyncio.wait_for(context.application.stop(), timeout=10.0)
        logger.info("Polling stopped.")

        # Close httpx client
        if hasattr(context.application, 'http'):
            logger.debug("Closing httpx client...")
            await context.application.http.aclose()
            logger.info("httpx client closed.")

        # Shut down the application
        logger.debug("Calling application.shutdown()...")
        await asyncio.wait_for(context.application.shutdown(), timeout=10.0)
        logger.info("Application fully shut down.")

        # Cancel remaining tasks
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            logger.debug("Cancelling task: %s", task.get_name())
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        logger.info("All tasks cancelled.")

        # Stop and close the event loop
        loop = asyncio.get_running_loop()
        loop.stop()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        logger.info("Event loop closed.")
    except asyncio.TimeoutError:
        logger.error("Shutdown timed out after 10 seconds, forcing termination.")
        await update.message.reply_text("⚠️ Shutdown timed out, forcing termination.")
        loop = asyncio.get_running_loop()
        loop.stop()
        loop.run_until_complete(loop.shutdown_asyncgens())
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
    msg += f"Nickname: {user_data.get('nickname', 'Not set')}\n"
    msg += f"Emoji: {user_data['emoji']}\n"
    msg += f"Gems: {user_data['gems']}\n"
    msg += f"Gold: {user_data.get('gold', 0)}\n"
    msg += f"Tiles Placed: {user_data['tiles_count']}\n"
    msg += f"Admin: {'Yes' if user_data['admin'] else 'No'}\n"
    msg += f"Santa: {'Yes' if user_data['santa'] else 'No'}\n"
    msg += f"Canvas: {user_data['canvas']}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")
    logger.info("Sent profile to %s.", user.full_name)


async def santa_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /santa [join|who|status|assign|reset]
    Manages Secret Santa participation and assignments.
    """
    user = update.effective_user
    user_service = UserService(users_dir=USERS_DIR)
    santa_service = SantaService(user_service)
    args = context.args

    if not args:
        await update.message.reply_text(
            "🎅 Secret Santa Commands:\n"
            "`/santa join` - Join the Secret Santa event.\n"
            "`/santa who` - See your assigned giftee and participants.\n"
            "`/santa status` - Check your participation status and participants.\n"
            "`/santa assign` - Assign Secret Santa pairs (admin-only).\n"
            "`/santa reset` - Reset the Secret Santa event (admin-only)."
        )
        return

    command = args[0].lower()

    if command == "join":
        if santa_service.join_santa(user.id):
            await update.message.reply_text("🎅 You’ve joined the Secret Santa event!")
        else:
            await update.message.reply_text("❌ You need to register first with /start.")
        logger.info("User %s (%s) requested to join Secret Santa.", user.full_name, user.id)

    elif command == "who":
        if not user_service.get_user(user.id):
            await update.message.reply_text("❌ You need to register first with /start.")
            return
        if not user_service.get(user.id, "santa", False):
            await update.message.reply_text("❌ You’re not participating in Secret Santa. Use /santa join.")
            return
        giftee_id, participants = santa_service.get_pair(user.id)
        participants_str = ", ".join(participants) if participants else "None"
        if giftee_id:
            giftee = user_service.get_user(giftee_id)
            nickname = giftee.get('nickname', giftee['username'])
            await update.message.reply_text(
                f"🎁 Your Secret Santa giftee is {nickname} (ID: {giftee_id}).\n"
                f"Participants: {participants_str}"
            )
        else:
            await update.message.reply_text(
                f"🕒 No giftee assigned yet (not enough participants).\n"
                f"Participants: {participants_str}"
            )
        logger.info("User %s (%s) checked their Secret Santa giftee.", user.full_name, user.id)

    elif command == "status":
        if not user_service.get_user(user.id):
            await update.message.reply_text("❌ You need to register first with /start.")
            return
        is_participating = user_service.get(user.id, "santa", False)
        status = "participating" if is_participating else "not participating"
        giftee_id, participants = santa_service.get_pair(user.id)
        participants_str = ", ".join(participants) if participants else "None"
        pair_status = f", assigned to {giftee_id}" if giftee_id else ", no giftee assigned yet"
        await update.message.reply_text(
            f"🎅 You are {status}{pair_status}.\n"
            f"Participants: {participants_str}"
        )
        logger.info("User %s (%s) checked Secret Santa status.", user.full_name, user.id)

    elif command == "assign":
        if not user_service.is_admin(user.id):
            await update.message.reply_text("❌ Only admins can assign Secret Santa pairs.")
            logger.warning("Non-admin %s (%s) attempted to assign Santa pairs.", user.full_name, user.id)
            return
        pairs = santa_service.assign_pairs()
        if not pairs:
            await update.message.reply_text("❌ Not enough participants to assign pairs (need at least 2).")
        else:
            participants = santa_service.get_participant_names()
            await update.message.reply_text(
                f"🎅 Assigned {len(pairs)} Secret Santa pairs.\n"
                f"Participants: {', '.join(participants)}"
            )
        logger.info("Admin %s (%s) assigned Secret Santa pairs.", user.full_name, user.id)

    elif command == "reset":
        if not user_service.is_admin(user.id):
            await update.message.reply_text("❌ Only admins can reset the Secret Santa event.")
            logger.warning("Non-admin %s (%s) attempted to reset Santa event.", user.full_name, user.id)
            return
        santa_service.reset_santa()
        await update.message.reply_text("🎅 Secret Santa event has been reset.")
        logger.info("Admin %s (%s) reset Secret Santa event.", user.full_name, user.id)

    else:
        await update.message.reply_text("❌ Unknown subcommand. Use /santa for help.")


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

COMMAND_HANDLERS = {
    "start": start,
    "help": help_command,
    "users": users_command,
    "gems": gems_command,
    "gold": gold_command,
    "stop": stop_command,
    "myprofile": myprofile_command,
    "santa": santa_command
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
