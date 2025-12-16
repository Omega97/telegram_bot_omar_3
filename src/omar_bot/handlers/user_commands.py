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


def register_command(name, admin_only=False):
    """Decorator for registering commands to the COMMAND_HANDLERS variable."""

    def decorator(func):
        # Extract and clean the docstring
        raw_doc = func.__doc__ or ""
        # Collapse consecutive whitespace and replace \n with " - "
        description = " ".join(line.strip() for line in raw_doc.splitlines() if line.strip())

        # Wrap with admin check if needed
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
            "description": description,
            "admin_only": admin_only
        }
        return final_handler

    return decorator


# ===== User commands =====


@register_command("start")
async def start(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Sends a welcome message with the user's name."""
    user = update.effective_user
    logger.info(f"User {user.full_name} started the bot.")

    name = user.full_name.split(" ")[0]
    msg = f"Hello, {name}! I am an echo bot. Type anything and I'll repeat it back to you."
    await update.message.reply_text(msg)
    logger.info(f"Sent a welcome message to user {user.full_name}.")


@register_command("help")
async def help_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Sends a help message with a list of available commands."""
    user = update.effective_user
    logger.info(f"User {user.full_name} requested help.")

    service = UserService(users_dir=USERS_DIR)
    is_admin = service.is_admin(user.id)

    # Separate commands by permission
    regular_lines = []
    admin_lines = []

    for name, info in COMMAND_HANDLERS.items():
        desc = info["description"]
        admin_only = info["admin_only"]

        # Format as `/command - Description`
        line = f"`/{name}` - {desc}"

        if admin_only:
            admin_lines.append(line)
        else:
            regular_lines.append(line)

    # Build help text
    help_text = "**Available Commands** 📖\n"
    help_text += "\n".join(sorted(regular_lines))

    if is_admin and admin_lines:
        help_text += "\n\n**Admin Commands** ✨\n"
        help_text += "\n".join(sorted(admin_lines))

    await update.message.reply_text(help_text, parse_mode="Markdown")
    logger.info(f"Sent help message to user {user.full_name} ({user.id}).")


@register_command("users")
async def users_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Displays the IDs, emoji, and nicknames of all users."""
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


@register_command("gems")
async def gems_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """
    Displays the IDs, emojis, nicknames, and gems of all users,
    sorted by gems in descending order.
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


@register_command("gold")
async def gold_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Displays the IDs, emojis, nicknames, and gold of all users."""
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


@register_command("myprofile")
async def myprofile_command(update: Update, _: ContextTypes.DEFAULT_TYPE):
    """Shows the user's profile information."""
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


@register_command("santa")
async def santa_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tells you you santa for this Christmas."""
    user = update.effective_user
    user_service = UserService(users_dir=USERS_DIR)

    # Ensure user is registered
    if not user_service.get_user(user.id):
        await update.message.reply_text("❌ You need to register first with /start.")
        return

    args = context.args
    if not args:
        # Show help
        is_admin = user_service.is_admin(user.id)
        santa_service = SantaService(user_service)
        help_text = santa_service.get_help_text(admin=is_admin)
        await update.message.reply_text(help_text, parse_mode="Markdown")
        return

    subcommand = args[0].lower()

    # --- Admin-only commands ---
    if subcommand in ("join", "kick"):
        if not user_service.is_admin(user.id):
            await update.message.reply_text("❌ Only admins can manage Secret Santa members.")
            return

        if len(args) != 3:
            await update.message.reply_text(
                f"❌ Usage: `/santa {subcommand} [user_id] [group_name]`\n"
                "Group name must start with `santa` (e.g., `santa_xmas2025`)."
            )
            return

        try:
            target_user_id = int(args[1])
            group_name = args[2].strip()
        except ValueError:
            await update.message.reply_text("❌ User ID must be a number.")
            return

        if not user_service.get_user(target_user_id):
            await update.message.reply_text(f"❌ User `{target_user_id}` not found.")
            return

        # Validate and normalize group name
        try:
            validated_group = SantaService.validate_group_name(group_name)
        except ValueError as e:
            await update.message.reply_text(f"❌ {e}")
            return

        santa_service = SantaService(user_service)

        if subcommand == "join":
            santa_service.admin_join_user_to_group(target_user_id, validated_group)
            await update.message.reply_text(f"✅ Added user `{target_user_id}` to group `{validated_group}`.")
        else:  # kick
            santa_service.admin_kick_user_from_group(target_user_id, validated_group)
            await update.message.reply_text(f"✅ Removed user `{target_user_id}` from group `{validated_group}`.")
        return

    # --- Public & mixed commands ---

    # --- /santa who [optional_group] ---
    if subcommand == "who":
        # Check if group is specified
        specified_group = None
        if len(args) > 1:
            specified_group = args[1].strip().lower()
            if not specified_group.startswith("santa"):
                await update.message.reply_text("❌ Group name must start with `santa`.")
                return

        santa_service = SantaService(user_service)
        all_groups = santa_service.get_user_santa_groups(user.id)

        if not all_groups:
            await update.message.reply_text(
                "❌ You are not in any Secret Santa group.\n"
                "Please contact an admin to be added to one."
            )
            return

        # If group specified, use it (if user is in it)
        if specified_group:
            if specified_group not in all_groups:
                await update.message.reply_text(f"❌ You are not in group `{specified_group}`.")
                return
            target_groups = [specified_group]
        else:
            target_groups = all_groups

        # Handle single vs multiple
        if len(target_groups) == 1:
            group = target_groups[0]
            santa_service = SantaService(user_service, group_name=group)
            giftee_id = santa_service.get_giftee(user.id)
            participants = santa_service.get_participant_names()
            participants_str = ", ".join(participants) if participants else "None"

            if giftee_id:
                giftee_name = user_service.get_user(giftee_id)["username"]
                msg = f"🎁 Your giftee in group `{group}` is **{giftee_name}**.\nParticipants: {participants_str}"
            else:
                msg = (f"🕒 No giftee assigned yet in group `{group}` (not enough participants).\n"
                       f"Participants: {participants_str}")
            await update.message.reply_text(msg, parse_mode="Markdown")
        else:
            group_list = "\n".join(f"`{g}`" for g in all_groups)
            await update.message.reply_text(
                f"🎅 You belong to **{len(all_groups)}** Secret Santa groups:\n{group_list}\n\n"
                "Please specify one: `/santa who [group_name]`"
            )
        return

    # --- /santa groups ---
    elif subcommand == "groups":
        santa_service = SantaService(user_service)
        groups = santa_service.get_user_santa_groups(user.id)

        if not groups:
            await update.message.reply_text(
                "❌ You are not in any Secret Santa group.\n"
                "Please contact an admin to be added to one."
            )
        else:
            group_list = "\n".join(f"`{g}`" for g in groups)
            await update.message.reply_text(
                f"🎅 You are in **{len(groups)}** Secret Santa group(s):\n{group_list}",
                parse_mode="Markdown"
            )
        return

    # --- /santa reset [optional_group] ---
    if subcommand == "reset":
        if not user_service.is_admin(user.id):
            await update.message.reply_text("❌ Only admins can reset Secret Santa groups.")
            return

        santa_service = SantaService(user_service)

        if len(args) == 1:
            # List all groups
            groups = santa_service.reset_santa()  # returns list when no arg
            if groups:
                group_list = "\n".join(f"`{g}`" for g in sorted(groups))
                msg = f"🎅 **Existing Santa groups:**\n{group_list}\n\nUse `/santa reset [group]` to delete one."
            else:
                msg = "🎅 No Santa groups found."
            await update.message.reply_text(msg, parse_mode="Markdown")
            return

        elif len(args) == 2:
            # Delete specific group
            group_name = args[1].strip().lower()
            try:
                validated_group = SantaService.validate_group_name(group_name)
            except ValueError as e:
                await update.message.reply_text(f"❌ {e}")
                return

            errors = santa_service.reset_santa(validated_group)
            if errors:
                await update.message.reply_text(f"❌ {' '.join(errors)}")
            else:
                await update.message.reply_text(f"✅ Santa group `{validated_group}` has been deleted!")
            return
        else:
            await update.message.reply_text(
                "❌ Usage:\n"
                "`/santa reset` → list all Santa groups\n"
                "`/santa reset [group]` → delete a specific group"
            )
            return

    # --- Unknown command ---
    is_admin = user_service.is_admin(user.id)
    santa_service = SantaService(user_service)
    await update.message.reply_text(
        "❌ Unknown subcommand.\n" + santa_service.get_help_text(admin=is_admin),
        parse_mode="Markdown"
    )


@register_command("place")
async def place_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View the current canvas or place a tile at the given coordinates."""
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


@register_command("roll")
async def roll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Rolls N dice with M sides each."""
    args = context.args
    if not args:
        help_text = (
            "🎲 **Dice Roll Command**\n"
            "Usage: `/roll NdM`\n\n"
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


@register_command("draw")
async def draw_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """ Draw black and white tokens from a bag."""
    user = update.effective_user
    args = context.args
    if len(args) != 3:
        await update.message.reply_text(
            "❌ Usage: `/draw [n_black] [n_white] [n_draws]`\n"
            "Example: `/draw 5 3 4`"
        )
        return

    try:
        n_black = int(args[0])
        n_white = int(args[1])
        n_draws = int(args[2])
    except ValueError:
        await update.message.reply_text("❌ All arguments must be non-negative integers.")
        return

    if n_black < 0 or n_white < 0 or n_draws < 0:
        await update.message.reply_text("❌ Counts must be ≥ 0.")
        return

    total = n_black + n_white
    if n_draws == 0:
        await update.message.reply_text("ℹ️ Drew 0 tokens. Nothing to show!")
        return

    if n_draws > total:
        await update.message.reply_text(
            f"❌ Cannot draw {n_draws} tokens from a bag of only {total} tokens!"
        )
        return

    # Build bag: list of black and white tokens
    bag = ["⚫️"] * n_black + ["⚪️"] * n_white

    # Shuffle and draw
    random.shuffle(bag)
    drawn = sorted(bag[:n_draws])

    black_count = drawn.count("⚫️")
    white_count = drawn.count("⚪️")

    result_line = "".join(drawn)
    display_line = f"({'⚪️' * n_white}{'⚫️' * n_black}) ➡️ {result_line}"
    summary = f"White: {white_count} | Black: {black_count}"
    msg = f"Drawn {n_draws} tokens\n{display_line}\n{summary}"

    # ✅ Log to console
    logger.info(f"User {user.full_name} ({user.id}) drew {display_line}")

    await update.message.reply_text(msg)
