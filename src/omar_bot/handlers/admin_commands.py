import logging
from telegram import Update
from telegram.ext import ContextTypes
import asyncio
from omar_bot.services.user_service import UserService
from omar_bot.config.settings import USERS_DIR
from omar_bot.services.place import PlaceService


# Get a logger instance for this module
logger = logging.getLogger(__name__)


def admin_only(handler):
    """Decorator to restrict command access to admins only."""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user = update.effective_user
        service = UserService(users_dir=USERS_DIR)
        if not service.is_admin(user.id):
            await update.message.reply_text("❌ Only administrators can use this command.")
            logger.warning(
                "Non-admin user %s (%s) attempted to access admin command: %s",
                user.full_name, user.id, handler.__name__
            )
            return
        return await handler(update, context)
    return wrapper


@admin_only
async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /stop
    Gracefully stops the bot.
    """
    user = update.effective_user
    logger.info("User %s (%s) requested bot shutdown.", user.full_name, user.id)

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


@admin_only
async def set_canvas_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /set_canvas [user_id] [canvas_name]
    Admin command to set a user's canvas.
    """
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


@admin_only
async def reset_canvas_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /reset_canvas [canvas_name]
    Admin command to reset a canvas to empty state.
    """
    args = context.args
    canvas_name = args[0] if args else "default"

    # Ask for confirmation
    confirmation_text = (f"⚠️ **WARNING**\nAre you sure you want to reset the canvas '{canvas_name}'?\n"
                         f"This will clear all tiles!\nReply with 'yes' to confirm.")
    await update.message.reply_text(confirmation_text, parse_mode="Markdown")

    # Store the canvas name in context for the confirmation handler
    context.user_data['reset_canvas_pending'] = canvas_name


@admin_only
async def delete_canvas_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /delete_canvas [canvas_name]
    Admin command to delete a canvas file.
    """
    args = context.args
    canvas_name = args[0] if args else "default"

    # Ask for confirmation
    confirmation_text = (f"⚠️ **DANGER**\nAre you sure you want to DELETE the canvas file '{canvas_name}'?\n"
                         f"This action cannot be undone!\nReply with 'yes' to confirm.")
    await update.message.reply_text(confirmation_text, parse_mode="Markdown")

    # Store the canvas name in context for the confirmation handler
    context.user_data['delete_canvas_pending'] = canvas_name


@admin_only
async def set_emoji_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """ /set_emoji [user_id] [emoji]
    Admin command to manually set a user's emoji.
    """
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
    logger.info("Admin %s set emoji for user %s to %s", update.effective_user.full_name, target_user_id, new_emoji)


async def canvas_confirmation_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle confirmation responses for canvas reset/delete commands.
    Ignore non-text or missing messages (e.g., edits of media, or unexpected updates)
    """
    message = update.effective_message
    if not message or not message.text:
        return

    text = message.text.lower().strip()

    # Handle reset canvas confirmation
    if 'reset_canvas_pending' in context.user_data:
        canvas_name = context.user_data['reset_canvas_pending']
        del context.user_data['reset_canvas_pending']

        if text == 'yes':
            user_service = UserService(users_dir=USERS_DIR)
            place_service = PlaceService(user_service)
            success = place_service.reset_canvas(canvas_name)

            if success:
                await update.message.reply_text(f"✅ Canvas '{canvas_name}' has been reset!")
            else:
                await update.message.reply_text(f"❌ Failed to reset canvas '{canvas_name}'")
        else:
            await update.message.reply_text("❌ Canvas reset cancelled.")
        return

    # Handle delete canvas confirmation
    if 'delete_canvas_pending' in context.user_data:
        canvas_name = context.user_data['delete_canvas_pending']
        del context.user_data['delete_canvas_pending']

        if text == 'yes':
            user_service = UserService(users_dir=USERS_DIR)
            place_service = PlaceService(user_service)
            success = place_service.delete_canvas(canvas_name)

            if success:
                await update.message.reply_text(f"✅ Canvas '{canvas_name}' has been deleted!")
            else:
                await update.message.reply_text(f"❌ Failed to delete canvas '{canvas_name}'")
        else:
            await update.message.reply_text("❌ Canvas deletion cancelled.")
        return


# Exports (add here new commands)
__all__ = ['admin_only', 'stop_command', 'set_canvas_command',
           'reset_canvas_command', 'delete_canvas_command',
           'set_emoji_command', 'canvas_confirmation_handler']
