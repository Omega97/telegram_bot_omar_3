# src/omar_bot/command_registry.py
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from omar_bot.services.user_service import UserService
from omar_bot.config.settings import USERS_DIR


# Global registry for all commands
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
