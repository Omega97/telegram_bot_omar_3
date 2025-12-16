"""
User Command Handlers
"""
import logging
from functools import wraps
import re
import random
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from omar_bot.config.settings import USERS_DIR
from omar_bot.services.place import PlaceService
from omar_bot.services.santa_v2 import SantaService
from omar_bot.services.user_service import UserService
from omar_bot.core.message_processor import process_message


# Get a logger instance for this module
logger = logging.getLogger(__name__)


# List of commands (handler, description, admin_only)
COMMAND_HANDLERS = {}


def register_command(name, description=None, admin_only=False):
    """Decorator for registering commands to the COMMAND_HANDLERS variable."""
    def decorator(func):
        # If admin_only is True, wrap the handler with admin check logic
        if admin_only:
            @wraps(func)
            async def admin_wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
                user = update.effective_user
                service = UserService(users_dir=USERS_DIR)
                if not service.is_admin(user.id):
                    await update.message.reply_text("❌ Admin-only command.")
                    return None
                return await func(update, context)
            final_handler = admin_wrapper
        else:
            final_handler = func

        COMMAND_HANDLERS[name] = {
            "handler": final_handler,
            "description": description or func.__doc__,
            "admin_only": admin_only
        }
        return final_handler
    return decorator


# ===== User commands =====


@register_command("start", "Greet the bot and get a welcome message")
async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """ /start
    Sends a welcome message with the user's name.
    """
    user = update.effective_user
    logger.info(f"User {user.full_name} started the bot.")

    name = user.full_name.split(" ")[0]
    msg = f"Hello, {name}! I am an echo bot. Type anything and I'll repeat it back to you."
    await update.message.reply_text(msg)
    logger.info(f"Sent a welcome message to user {user.full_name}.")


@register_command("help",
                  "Get a list of available commands and their descriptions")
async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """ /help
    Sends a help message. Shows admin commands only to admins.
    """
    user = update.effective_user
    logger.info(f"User {user.full_name} requested help.")

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
    logger.info(f"Sent help message to user {user.full_name} ({user.id}).")


@register_command("users",
                  "Show the list of all users by nickname")
async def users_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """ /users
    Displays the IDs, emojis, and nicknames of all users.
    """
    user = update.effective_user
    logger.info(f"User {user.full_name} requested the user list.")

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
    logger.info(f"Sent the user list to {user.full_name}.")


@register_command("gems",
                  "Show the list of all users with their gems, sorted by gems")
async def gems_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """ /gems
    Displays the IDs, emojis, nicknames, and gems of all users, sorted by gems in descending order.
    Filter out players with 0 gems
    """
    user = update.effective_user
    logger.info(f"User {user.full_name} requested the gems list.", )

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
    logger.info(f"Sent the gems list to {user.full_name}.", )


@register_command("gold",
                  "Show the list of all users with their gold")
async def gold_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """ /gold
    Displays the IDs, emojis, nicknames, and gold of all users.
    """
    user = update.effective_user
    logger.info(f"User {user.full_name} requested the gold list.")

    service = UserService(users_dir=USERS_DIR)
    user_ids = service.get_user_ids()
    user_ids = [uid for uid in user_ids if service.get_user(uid).get('gold', 0)]

    if not user_ids:
        msg = "No users found."
    else:
        msg = f"{len(user_ids)} users with gold 🟡:\n"
        for i, uid in enumerate(user_ids):
            user_data = service.get_user(uid)
            nickname = user_data.get('nickname', user_data.get('username', 'Unknown'))
            emoji = user_data.get('emoji', '')
            gold = user_data.get('gold', 0)
            if gold:
                msg += f"{emoji} {nickname}:  {gold}\n"

    await update.message.reply_text(msg, parse_mode="Markdown")
    logger.info(f"Sent the gold list to {user.full_name}.")


@register_command("myprofile",
                  "Shows your profile info")
async def myprofile_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """ /myprofile
    Shows the user's profile information.
    """
    user = update.effective_user
    logger.info(f"User {user.full_name} requested their profile.")
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
    logger.info(f"Sent profile to {user.full_name}.")


@register_command("santa",
                  "Manage Secret Santa participation and assignments")
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
        logger.info(f"User {user.full_name} ({user.id}) requested to join Secret Santa.")

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
        logger.info(f"User {user.full_name} ({user.id}) checked their Secret Santa giftee.")

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
        logger.info(f"User {user.full_name} ({user.id}) checked Secret Santa status.")

    elif command == "reset":
        # Resets the Secret Santa event by clearing all pairings and participation.
        if not user_service.is_admin(user.id):
            await update.message.reply_text("❌ Only admins can reset the Secret Santa event.")
            logger.warning(f"Non-admin {user.full_name} ({user.id}) attempted to reset Santa event.")
            return
        santa_service.reset_santa()
        await update.message.reply_text("🎅 Secret Santa event has been reset.")
        logger.info(f"Admin {user.full_name} ({user.id}) reset Secret Santa event.")

    else:
        # Unknown subcommand
        await update.message.reply_text("❌ Unknown subcommand. Use /santa for help.")


@register_command("place",
                  "Place or view tiles on the canvas")
async def place_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ /place [x] [y] – Shows canvas or places a tile. """
    user = update.effective_user
    logger.info(f"User {user.full_name} requested place command.")

    service = UserService(users_dir=USERS_DIR)
    place_service = PlaceService(service)

    # Early check: is user registered?
    if not service.get_user(user.id):
        await update.message.reply_text("❌ You need to register first with /start.")
        return

    args = context.args
    if not args:
        # View-only mode
        resp = place_service.get_place_response(user.id)
        if "error" in resp:
            await update.message.reply_text("❌ Unexpected error.")
            return

        msg = f"🎨 **Current Canvas: {resp['canvas_name']}**\n```\n{resp['canvas_display']}\n```\n"
        msg += f"🧱 Tiles placed: {resp['tiles_count']}\n"
        msg += f"💎 Gems: {resp['gems']}\n"
        msg += f"⏱️ Cooldown: {resp['cooldown_minutes']} minutes\n\n{resp['time_info']}"

        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    # Placement mode
    if len(args) != 2:
        await update.message.reply_text("❌ Usage: /place [x] [y]\nExample: /place 5 3")
        return

    try:
        x = int(args[0])
        y = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ Coordinates must be numbers!")
        return

    resp = place_service.attempt_place_tile(user.id, x, y)

    if resp["success"]:
        msg = f"{resp['message']}\n\n🎨 **Updated Canvas**\n```\n{resp['canvas_display']}\n```\n"
        msg += f"Your tiles: {resp['tiles_count']}  💎 Gems: {resp['gems']}"
        await update.message.reply_text(msg, parse_mode="Markdown")
    else:
        await update.message.reply_text(f"❌ {resp['message']}")

    logger.info(f"User {user.full_name} attempted to place tile at ({x}, {y}): "
                f"{'success' if resp['success'] else 'failed'}")


@register_command("roll", "Roll dice using notation like '2d6' or '1d20'")
async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /roll [NdM]
    Rolls N dice with M sides each.
    Examples:
      /roll 1d20  → rolls one 20-sided die
      /roll 2d6   → rolls two 6-sided dice
      /roll       → shows usage instructions
    """
    args = context.args
    if not args:
        help_text = (
            "🎲 **Dice Roll Command**\n"
            "Usage: `/roll NdM`\n"
            "• `N` = number of dice (default: 1)\n"
            "• `M` = number of sides per die (e.g. 6, 20)\n\n"
            "**Examples**:\n"
            "`/roll d20`  → roll one 20-sided die\n"
            "`/roll 2d6`  → roll two 6-sided dice\n"
            "`/roll 3d8+5` → roll 3d8 and add 5 (bonus)"
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
        return

    # Join all args into a single string (in case of spaces)
    dice_expr = " ".join(args).strip()

    # Support formats: "d20", "1d20", "2d6", "3d8+5", etc.
    # Regex explanation:
    #   ^\s*                – optional leading whitespace
    #   (\d+)?              – optional number of dice (group 1)
    #   d                   – literal 'd'
    #   (\d+)               – required number of sides (group 2)
    #   (?:\s*([+-])\s*(\d+))? – optional bonus: +5 or -3 (groups 3 and 4)
    #   \s*$                – optional trailing whitespace
    match = re.match(r"^\s*(\d+)?d(\d+)(?:\s*([+-])\s*(\d+))?\s*$", dice_expr, re.IGNORECASE)

    if not match:
        await update.message.reply_text(
            "❌ Invalid format.\n"
            "Use: `/roll NdM` (e.g. `1d20`, `2d6`)\n"
            "You can also add a bonus: `2d6+3`"
        )
        return

    num_dice_str, sides_str, bonus_op, bonus_str = match.groups()
    num_dice = int(num_dice_str) if num_dice_str else 1
    sides = int(sides_str)
    bonus = int(bonus_str) if bonus_str else 0
    if bonus_op == "-":
        bonus = -bonus

    # Validate
    if num_dice < 1:
        await update.message.reply_text("❌ Number of dice must be ≥ 1")
        return
    if sides < 2:
        await update.message.reply_text("❌ Dice must have ≥ 2 sides")
        return
    if num_dice > 100:
        await update.message.reply_text("❌ Too many dice! Max: 100")
        return
    if sides > 1000:
        await update.message.reply_text("❌ Dice too big! Max sides: 1000")
        return

    # Roll dice
    rolls = [random.randint(1, sides) for _ in range(num_dice)]
    total = sum(rolls) + bonus

    # Build message
    dice_notation = f"{num_dice}d{sides}"
    if bonus != 0:
        dice_notation += f"{'+' if bonus > 0 else ''}{bonus}"

    if num_dice == 1:
        result_text = f"**Roll**: {rolls[0]}"
    else:
        rolls_str = ", ".join(str(r) for r in rolls)
        result_text = f"**Rolls**: {rolls_str}\n**Sum**: {sum(rolls)}"

    if bonus != 0:
        result_text += f" {'+' if bonus > 0 else '-'} {abs(bonus)} → **Total**: {total}"

    msg = f"🎲 Rolling **{dice_notation}**\n{result_text}"
    await update.message.reply_text(msg, parse_mode="Markdown")


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
