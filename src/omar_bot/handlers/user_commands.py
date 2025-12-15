"""
User Command Handlers
"""
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, ContextTypes, filters
from datetime import datetime
from omar_bot.services.santa_v2 import SantaService
from omar_bot.services.place import PlaceService
from omar_bot.config.settings import USERS_DIR
from omar_bot.config.settings import PLACE_COOLDOWN_MINUTES
from omar_bot.services.user_service import UserService
from omar_bot.handlers.admin_commands import stop_command


# Get a logger instance for this module
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /start
    Sends a welcome message with the user's name.
    """
    user = update.effective_user
    logger.info("User %s started the bot.", user.full_name)
    name = user.full_name.split(" ")[0]
    msg = f"Hello, {name}! I am an echo bot. Type anything and I'll repeat it back to you."
    await update.message.reply_text(msg)
    logger.info("Sent a welcome message to user %s.", user.full_name)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /help
    Sends a help message. Shows admin commands only to admins.
    """
    user = update.effective_user
    logger.info("User %s requested help.", user.full_name)

    # Determine if the user is an admin
    service = UserService(users_dir=USERS_DIR)
    is_admin = service.is_admin(user.id)

    regular_commands = (
        "`/start` - Greet the bot and get a welcome message.",
        "`/help` - Get a list of available commands and their descriptions.",
        "`/users` - Show the list of all users by nickname.",
        "`/gems` - Show the list of all users with their gems.",
        "`/gold` - Show the list of all users with their gold.",
        "`/myprofile` - Shows your profile info.",
        "`/place` - Show the current canvas and your tile status.",
        "`/place [x] [y]` - Place a tile at coordinates (x, y).",
        "`/santa` - Manage Secret Santa participation and assignments.",
        "`/santa join` - Join the Secret Santa event.",
        "`/santa who` - See your assigned giftee and participants.",
        "`/santa status` - Check your participation status and participants.",
    )

    admin_commands = (
        "`/stop` - Gracefully terminate the bot.",
        "`/set_emoji [user] [emoji]` - Manually set a user's emoji.",
        "`/set_canvas [user] [canvas]` - Change a user's canvas.",
        "`/reset_canvas [canvas]` - Clear all tiles from a canvas.",
        "`/delete_canvas [canvas]` - Permanently delete a canvas file.",
        "`/santa reset` - Reset the Secret Santa event (admin-only).",
    )

    # Start building the help text with regular commands
    help_text = f"**Available Commands** 📖\n"
    help_text += "\n".join(regular_commands)
    if is_admin:
        help_text += f"\n\n**Admin Commands** ✨\n"
        help_text += "\n".join(admin_commands)

    # Send the help message
    await update.message.reply_text(help_text, parse_mode="Markdown")
    logger.info("Sent help message to user %s (%s).", user.full_name, user.id)


async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def gems_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /gems
    Displays the IDs, emojis, nicknames, and gems of all users, sorted by gems in descending order.
    Filter out players with 0 gems
    """
    user = update.effective_user
    logger.info("User %s requested the gems list.", user.full_name)
    service = UserService(users_dir=USERS_DIR)
    user_ids = service.get_user_ids()

    # Filter users who have gems > 0
    user_ids_with_gems = [uid for uid in user_ids if service.get_user(uid).get('gems', 0) > 0]

    if not user_ids_with_gems:
        msg = "No users found."
    else:
        # Sort the filtered user IDs by their gem count in descending order
        sorted_user_ids = sorted(user_ids_with_gems, key=lambda uid: service.get_user(uid).get('gems', 0), reverse=True)

        # Build the message string
        msg_lines = []
        for uid in sorted_user_ids:
            user_data = service.get_user(uid)
            nickname = user_data.get('nickname', user_data.get('username', 'Unknown'))
            emoji = user_data.get('emoji', '')
            gems = user_data.get('gems', 0)
            msg_lines.append(f"{gems:7}  {emoji}  {nickname}")

        # Join the lines and wrap in Markdown code block
        msg_body = "\n".join(msg_lines)
        msg = f"💎 {len(sorted_user_ids)} users with gems:\n```\n{msg_body}\n```"

    await update.message.reply_text(msg, parse_mode="Markdown")
    logger.info("Sent the gems list to %s.", user.full_name)


async def gold_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
                msg += f"{emoji} {nickname}:  {gold}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")
    logger.info("Sent the gold list to %s.", user.full_name)


async def myprofile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


async def santa_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /santa [join|who|status|reset]
    Manages Secret Santa participation and assignments.
    Mixed permissions.
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
        giftee_id = santa_service.get_giftee(user.id)
        participants = santa_service.get_participant_names()
        participants_str = ", ".join(participants) if participants else "None"
        if giftee_id:
            giftee = user_service.get_user(giftee_id)
            # nickname = giftee.get('nickname', giftee['username'])
            await update.message.reply_text(
                f"🎁 Your Secret Santa giftee is {giftee['username']}.\n"
                f"Participants: {participants_str}"
            )
        else:
            await update.message.reply_text(
                f"🕒 No giftee assigned yet (not enough participants).\n"
                f"Participants: {participants_str}"
            )
        logger.info("User %s (%s) checked their Secret Santa giftee.", user.full_name, user.id)

    elif command == "status":
        # Check who is participating to the secret santa
        if not user_service.get_user(user.id):
            await update.message.reply_text("❌ You need to register first with /start.")
            return
        is_participating = user_service.get(user.id, "santa", False)
        status = "participating" if is_participating else "not participating"
        giftee_id = santa_service.get_giftee(user.id)
        participants = santa_service.get_participant_names()
        participants_str = ", ".join(participants) if participants else "None"
        pair_status = f", assigned to {giftee_id}" if giftee_id else ", no giftee assigned yet"
        await update.message.reply_text(
            f"🎅 You are {status}{pair_status}.\n"
            f"Participants: {participants_str}"
        )
        logger.info("User %s (%s) checked Secret Santa status.", user.full_name, user.id)

    elif command == "reset":
        # Resets the Secret Santa event by clearing all pairings and participation.
        if not user_service.is_admin(user.id):
            await update.message.reply_text("❌ Only admins can reset the Secret Santa event.")
            logger.warning("Non-admin %s (%s) attempted to reset Santa event.", user.full_name, user.id)
            return
        santa_service.reset_santa()
        await update.message.reply_text("🎅 Secret Santa event has been reset.")
        logger.info("Admin %s (%s) reset Secret Santa event.", user.full_name, user.id)

    else:
        # Unknown subcommand
        await update.message.reply_text("❌ Unknown subcommand. Use /santa for help.")


async def place_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /place [x] [y]
    Shows the current canvas or places a tile at the specified coordinates.
    """
    user = update.effective_user
    logger.info("User %s requested place command.", user.full_name)

    # Get user data
    service = UserService(users_dir=USERS_DIR)
    user_data = service.get_user(user.id)

    if not user_data:
        await update.message.reply_text("❌ You need to register first with /start.")
        return

    # Initialize place service
    place_service = PlaceService(service)

    # Get current canvas name
    canvas_name = user_data.get('canvas', 'default')

    args = context.args
    if not args:
        # Show current canvas
        canvas_display = place_service.get_canvas_display(canvas_name)
        last_place_time = user_data.get('last_place_time', 0)
        cooldown_minutes = PLACE_COOLDOWN_MINUTES

        # Calculate time remaining if on cooldown
        time_info = ""
        if last_place_time:
            time_since_last = datetime.now().timestamp() - last_place_time
            cooldown_seconds = cooldown_minutes * 60
            if time_since_last < cooldown_seconds:
                remaining = cooldown_seconds - time_since_last
                mins = int(remaining // 60)
                secs = int(remaining % 60)
                time_info = f"\n\n⏳ Cooldown: {mins}m {secs}s remaining"
            else:
                time_info = "\n\n✅ You can place a tile now!"

        msg = f"🎨 **Current Canvas: {canvas_name}**\n```\n{canvas_display}\n```\n"
        msg += f"🧱 Tiles placed: {user_data.get('tiles_count', 0)}\n"
        msg += f"💎 Gems: {user_data.get('gems', 0)}\n"
        msg += f"⏱️ Cooldown: {cooldown_minutes} minutes{time_info}"

        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    if len(args) != 2:
        await update.message.reply_text("❌ Usage: /place [x] [y]\nExample: /place 5 3")
        return

    try:
        x = int(args[0])
        y = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ Coordinates must be numbers!")
        return

    # Try to place the tile
    success, message = place_service.place_tile(user.id, canvas_name, x, y)

    if success:
        # Show updated canvas
        canvas_display = place_service.get_canvas_display(canvas_name)
        user_data = service.get_user(user.id)  # Refresh user data
        msg = f"{message}\n\n🎨 **Updated Canvas**\n```\n{canvas_display}\n```\n"
        msg += f"Your tiles: {user_data.get('tiles_count', 0)}  "
        msg += f"💎 Gems: {user_data.get('gems', 0)}"
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ {message}")

    logger.info("User %s placed tile at (%d, %d): %s", user.full_name, x, y, success)


# ----- Message Handlers -----


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Echoes the user's message back to them.
    Handles both new messages and edited messages.
    """
    # Determine if it's a new message or an edited message
    message = update.effective_message  # This safely gets message or edited_message
    if not message or not message.text:
        return  # Ignore non-text messages (e.g. edits of media)

    user = message.from_user
    if not user:
        return

    logger.info(f"{user.full_name}: {message.text}")
    reply = message.text
    await message.reply_text(reply)
    logger.info(reply)


# ----- Adding Handlers to Application -----


COMMAND_HANDLERS = {
    "start": start,
    "help": help_command,
    "users": users_command,
    "gems": gems_command,
    "gold": gold_command,
    "stop": stop_command,
    "myprofile": myprofile_command,
    "santa": santa_command,
    "place": place_command,
}


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

    # command handlers
    for name, method in COMMAND_HANDLERS.items():
        application.add_handler(CommandHandler(name, method))

    # todo replace with actual bot response
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
