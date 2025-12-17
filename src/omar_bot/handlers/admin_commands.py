import logging
from telegram import Update
from telegram.ext import ContextTypes
import asyncio
from omar_bot.services.user_service import UserService
from omar_bot.config.settings import USERS_DIR, CANVAS_DIR
from omar_bot.services.place import PlaceService
from omar_bot.command_registry import register_command


# Get a logger instance for this module
logger = logging.getLogger(__name__)


# ===== Admin commands =====


@register_command("stop", admin_only=True)
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gracefully stops the bot."""
    user = update.effective_user
    logger.info(f"User {user.full_name} ({user.id}) requested bot shutdown.")

    try:
        await update.message.reply_text("Bot is shutting down...")
        logger.info("Initiating bot shutdown...")

        # Log active tasks
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        logger.debug(f"Active tasks before shutdown: {[t.get_name() for t in tasks]}")

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
            logger.debug(f"Cancelling task: {task.get_name()}")
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
        logger.error(f"Failed to stop the bot: {e}", )
        await update.message.reply_text(f"❌ Error stopping the bot: {str(e)}")


@register_command("set_canvas", admin_only=True)
async def set_canvas_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually set a user's canvas."""
    args = context.args
    if len(args) != 2:
        await update.message.reply_text(
            "❌ Usage: /set_canvas [user_id] [canvas_name]\nExample: /set_canvas 123456789 default")
        return

    try:
        target_user_id = int(args[0])
        canvas_name = args[1].strip()
    except ValueError:
        await update.message.reply_text("❌ User ID must be a number!")
        return

    user_service = UserService(users_dir=USERS_DIR)
    place_service = PlaceService(user_service)

    # Check if user exists
    target_user = user_service.get_user(target_user_id)
    if not target_user:
        await update.message.reply_text(f"❌ User {target_user_id} not found!")
        return

    # Set the canvas
    success = place_service.set_user_canvas(target_user_id, canvas_name)
    if success:
        await update.message.reply_text(f"✅ Set canvas for user {target_user_id} to '{canvas_name}'")
    else:
        await update.message.reply_text(f"❌ Failed to set canvas for user {target_user_id}")


@register_command("reset_canvas", admin_only=True)
async def reset_canvas_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset a canvas."""
    args = context.args
    if len(args) == 0:
        await update.message.reply_text(
            "❌ Usage: `/reset_canvas [canvas_name]` → shows confirmation\n"
            "         `/reset_canvas [canvas_name] yes` → confirms reset"
        )
        return

    canvas_name = args[0].strip()
    confirmed = len(args) > 1 and args[1].lower() == "yes"

    if not confirmed:
        msg = (
            f"⚠️ **Reset Canvas: `{canvas_name}`**\n"
            f"Are you sure? This will clear all tiles.\n"
            f"Reply with:\n`/reset_canvas {canvas_name} yes`"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    # Confirmed — perform action
    user_service = UserService(users_dir=USERS_DIR)
    place_service = PlaceService(user_service)
    success = place_service.reset_canvas(canvas_name)

    if success:
        await update.message.reply_text(f"✅ Canvas `{canvas_name}` has been reset!")
    else:
        await update.message.reply_text(f"❌ Failed to reset canvas `{canvas_name}`")


@register_command("delete_canvas", admin_only=True)
async def delete_canvas_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a canvas."""
    args = context.args
    if len(args) == 0:
        await update.message.reply_text(
            "❌ Usage: `/delete_canvas [canvas_name]` → shows confirmation\n"
            "         `/delete_canvas [canvas_name] yes` → confirms deletion"
        )
        return

    canvas_name = args[0].strip()
    confirmed = len(args) > 1 and args[1].lower() == "yes"

    if not confirmed:
        msg = (
            f"⚠️ **DELETE CANVAS: `{canvas_name}`**\n"
            f"This action **cannot be undone** and will **permanently delete** the file.\n"
            f"Reply with:\n`/delete_canvas {canvas_name} yes`"
        )
        await update.message.reply_text(msg, parse_mode="Markdown")
        return

    # Confirmed — perform deletion
    user_service = UserService(users_dir=USERS_DIR)
    place_service = PlaceService(user_service)
    success = place_service.delete_canvas(canvas_name)

    if success:
        await update.message.reply_text(f"✅ Canvas `{canvas_name}` has been permanently deleted!")
    else:
        await update.message.reply_text(f"❌ Failed to delete canvas `{canvas_name}` — file may not exist.")


@register_command("set_emoji", admin_only=True)
async def set_emoji_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set a user's emoji."""
    args = context.args
    if len(args) != 2:
        await update.message.reply_text(
            "❌ Usage: `/set_emoji [user_id] [emoji]`\n"
            "Example: `/set_emoji 123456789 🟦`"
        )
        return

    try:
        target_user_id = int(args[0])
        new_emoji = args[1]
    except ValueError:
        await update.message.reply_text("❌ User ID must be a number!")
        return

    # Validate emoji (basic check: non-empty and not whitespace-only)
    if not new_emoji or new_emoji.strip() != new_emoji:
        await update.message.reply_text("❌ Emoji cannot be empty or only whitespace.")
        return

    # Get user service
    user_service = UserService(users_dir=USERS_DIR)

    # Check if user exists
    target_user = user_service.get_user(target_user_id)
    if not target_user:
        await update.message.reply_text(f"❌ User `{target_user_id}` not found!")
        return

    # Update emoji
    user_service.set(target_user_id, "emoji", new_emoji)

    username = target_user.get("username", "Unknown")
    await update.message.reply_text(
        f"✅ Emoji for user `{username}` (`{target_user_id}`) set to: {new_emoji}"
    )
    logger.info(f"Admin {update.effective_user.full_name} set emoji for user {target_user_id} to {new_emoji}")


@register_command("new_canvas", admin_only=True)
async def new_canvas_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Create a new canvas."""
    args = context.args
    if len(args) != 3:
        await update.message.reply_text(
            "❌ Usage: /new_canvas [canvas_name] [width] [height]\n"
            "Example: /new_canvas my_new_canvas 30 20"
        )
        return

    canvas_name = args[0].strip()
    try:
        width = int(args[1])
        height = int(args[2])
    except ValueError:
        await update.message.reply_text("❌ Width and height must be numbers!")
        return

    # Validate dimensions (optional, adjust limits as needed)
    if width <= 0 or height <= 0:
        await update.message.reply_text("❌ Please provide valid dimensions.")
        return

    user_service = UserService(users_dir=USERS_DIR)
    place_service = PlaceService(user_service)

    # Attempt to create the canvas
    success = place_service.create_canvas(canvas_name, width, height)

    if success:
        await update.message.reply_text(
            f"✅ New canvas '{canvas_name}' created successfully with dimensions {width}x{height}!"
        )
        logger.info(f"Admin {update.effective_user.full_name} created canvas '{canvas_name}'.")
    else:
        await update.message.reply_text(
            f"❌ Failed to create canvas '{canvas_name}'. Check logs for details."
        )
        logger.error(f"Admin {update.effective_user.full_name} failed to create canvas '{canvas_name}'.")


@register_command("canvas_list", admin_only=True)
async def canvas_list_command(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Admin command to list all canvas files in the canvases directory.
    """
    user = update.effective_user
    logger.info(f"Admin {user.full_name} ({user.id}) requested the canvas list.")

    try:
        # Get all .csv files
        canvas_files = list(CANVAS_DIR.glob("*.csv"))

        if not canvas_files:
            msg = "📋 No canvas files found in the directory."
        else:
            # Sort files for consistent output
            sorted_names = sorted([f.stem for f in canvas_files]) # Use stem to get name without '.csv'
            canvas_list_str = "\n".join([f"- {name}" for name in sorted_names])
            msg = f"📋 Found {len(canvas_files)} canvas file(s):\n{canvas_list_str}"

    except Exception as e:
        logger.error(f"Error listing canvases requested by admin {user.full_name} ({user.id}): {e}")
        msg = "❌ An error occurred while listing the canvases. Please check the logs."

    await update.message.reply_text(msg)
    logger.info(f"Sent canvas list response to admin {user.full_name}.")


@register_command("list_users", admin_only=True)
async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Admin command to list all users with their IDs and emojis.
    """
    user = update.effective_user
    logger.info(f"Admin {user.full_name} ({user.id}) requested the user list.")

    try:
        service = UserService(users_dir=USERS_DIR)
        user_ids = service.get_user_ids()

        if not user_ids:
            msg = "📋 No users found in the database."
        else:
            # Build the message string
            msg_lines = [f"📋 Found {len(user_ids)} user(s):"]
            for uid in user_ids:
                user_data = service.get_user(uid)
                username = user_data.get('username', 'Unknown')
                emoji = user_data.get('emoji', '👤') # Default emoji if not set
                # Format: ID (Emoji) Username
                msg_lines.append(f"{uid:11} ({emoji}) {username}")

            msg = "\n".join(msg_lines)

    except Exception as e:
        logger.error(f"Error listing users requested by admin {user.full_name} ({user.id}): {e}")
        msg = "❌ An error occurred while listing the users. Please check the logs."

    await update.message.reply_text(msg)
    logger.info(f"Sent user list response to admin {user.full_name}.")
