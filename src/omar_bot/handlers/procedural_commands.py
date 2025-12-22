import logging
import random
import hashlib
import json
from typing import List
from telegram import Update
from telegram.ext import ContextTypes
from src.omar_bot.command_registry import register_command
from src.omar_bot.config.settings import PRIVATE_DIR


# Get a logger instance for this module
logger = logging.getLogger(__name__)


class RecentTracker:
    def __init__(self, keyword: str):
        self.keyword = keyword
        self.file_path = PRIVATE_DIR / f"recent_{keyword}.json"

    def _compute_hash(self, text: str) -> str:
        """Computes a unique SHA-256 hash for a string."""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

    def load_recent_hashes(self) -> List[str]:
        """Loads the list of hashes from the JSON file."""
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def save_recent_hashes(self, hashes: List[str], total_count: int):
        """Saves hashes, keeping only half of the total samples to ensure variety."""
        max_size = max(1, total_count // 2)
        to_save = hashes[-max_size:]  # Keep the most recent ones
        with open(self.file_path, "w") as f:
            json.dump(to_save, f)

    def get_filtered_sample(self, all_items: List[str]) -> str:
        """Filters out recent items and picks a new random one."""
        recent_hashes = self.load_recent_hashes()

        # Create a map of {hash: original_text} for items not in recent list
        pool = []
        for item in all_items:
            h = self._compute_hash(item)
            if h not in recent_hashes:
                pool.append((item, h))

        # Fallback: if somehow everything is filtered (shouldn't happen with 50% logic)
        # or the file only had 1-2 items total.
        if not pool:
            selected_item = random.choice(all_items)
            selected_hash = self._compute_hash(selected_item)
        else:
            selected_item, selected_hash = random.choice(pool)

        # Update the recent list: append new hash and save
        recent_hashes.append(selected_hash)
        self.save_recent_hashes(recent_hashes, len(all_items))

        return selected_item


def create_random_resource_command(keyword: str):
    filename = f"random_{keyword}.txt"
    command_name = f"random_{keyword}"
    tracker = RecentTracker(keyword)  # Initialize tracker for this keyword

    async def cmd_handler(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
        path = PRIVATE_DIR / filename
        user = update.effective_user

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

            # Use the tracker to get a non-recent sample
            selected_item = tracker.get_filtered_sample(items)

            await update.message.reply_text(selected_item)
            logger.info(f"✅ Executed /{command_name} for {user.username}. Item: '{selected_item[:30]}...'")

        except Exception as e:
            logger.error(f"Error in {command_name}: {e}")
            await update.message.reply_text(f"❌ An error occurred while retrieving a {keyword}.")

    cmd_handler.__doc__ = f"Returns a random {keyword} from the private {keyword} file."
    register_command(command_name, admin_only=False)(cmd_handler)


# --- Generate the commands ---
create_random_resource_command("category")
create_random_resource_command("challenge")
create_random_resource_command("opinion")
create_random_resource_command("red_flag")
