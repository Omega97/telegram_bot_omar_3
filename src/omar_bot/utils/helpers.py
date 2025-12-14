""" Helper methods
- random emoji
"""
import random


# Emoji list from your original scripts/utils.py
DEFAULT_EMOJI = [
    "⬜️", "🟥", "🟧", "🟨", "🟩", "🟪", "⚪", "🟠", "🟡", "🟢", "🔵", "🟣",
    "🐶", "🐱", "🦊", "🐭", "🐹", "🐰", "🐻", "🐼", "🐯", "🦁", "🐬", "🐧",
    "🦖", "🍀", "⚡️", "🔥", "⭐️", "☀️", "🍎", "🍓", "🍒", "🍉", "🍕", "🍣",
    "⚽️", "🏀", "🥎", "💎", "💻", "🚀", "🍪", "🛑", "❇️"
]


def get_random_emoji() -> str:
    return random.choice(DEFAULT_EMOJI)
