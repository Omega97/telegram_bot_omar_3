import logging
import random
from telegram import Update
from telegram.ext import ContextTypes
from omar_bot.command_registry import register_command
from omar_bot.config.settings import PRIVATE_DIR


# Get a logger instance for this module
logger = logging.getLogger(__name__)


def create_random_resource_command(keyword: str):
    """
    Factory function to create and register random selection commands.
    Example: keyword="opinions" creates /random_opinion command.
    """
    # Determine the singular form for messages (e.g., "opinions" -> "opinion")
    filename = f"random_{keyword}.txt"
    command_name = f"random_{keyword}"

    async def cmd_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        path = PRIVATE_DIR / filename

        if not path.exists():
            logger.error(f"File not found: {path}")
            await update.message.reply_text(f"⚠️ Sorry, I couldn't find my book of {keyword} right now.")
            return

        try:
            items = []
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        items.append(line)

            if not items:
                await update.message.reply_text(f"🤔 I have no {keyword} at the moment!")
                return

            await update.message.reply_text(random.choice(items))

        except Exception as e:
            logger.error(f"Error reading {filename}: {e}")
            await update.message.reply_text(f"❌ An error occurred while retrieving a {keyword}.")

    # Set a docstring so the register_command decorator can extract a description
    cmd_handler.__doc__ = f"Returns a random {keyword} from the private {keyword} file."

    # Manually register the command
    register_command(command_name, admin_only=False)(cmd_handler)


# --- Generate the commands ---
create_random_resource_command("category")
create_random_resource_command("challenge")
create_random_resource_command("opinion")
create_random_resource_command("red_flag")
