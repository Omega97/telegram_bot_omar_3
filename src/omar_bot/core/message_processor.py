# src/omar_bot/core/message_processor.py
#todo implement core bot
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def process_message(user_id: int, username: str, text: str) -> Optional[str]:
    """
    Process a raw text message and return the bot's reply (or None to suppress reply).

    This function is pure logic — no Telegram types, no async, no side effects.
    It can be easily unit-tested and extended with NLP, commands, game logic, etc.

    Args:
        user_id: Telegram user ID
        username: Telegram username or full name
        text: Raw message text

    Returns:
        Reply string, or None if no reply should be sent.
    """
    # Example: simple echo (current behavior)
    return text

    # Future examples you could add:
    #
    # if text.lower() == "ping":
    #     return "pong"
    #
    # if text.startswith("!roll"):
    #     return handle_dice_roll(text)
    #
    # return run_llm_pipeline(user_id, text)  # e.g., integrate with AI
