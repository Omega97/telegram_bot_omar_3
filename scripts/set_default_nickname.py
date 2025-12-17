import logging
from pathlib import Path
from omar_bot.services.user_service import UserService
from omar_bot.config.settings import USERS_DIR


# Get a logger instance for this module
logger = logging.getLogger(__name__)


def compute_default_nickname(username: str, user_id: int) -> str:
    nickname = username.split()[0]
    nickname += str(user_id)[-3:]
    return nickname


def set_default_nicknames():  # Use module-specific logger
    command = input('Reset user nicknames? ')
    if command.lower() != 'y':
        return

    user_service = UserService(users_dir=Path(USERS_DIR))
    user_ids = user_service.get_user_ids()
    if not user_ids:
        logger.info("No users found in %s.", USERS_DIR)
        return

    logger.info("Processing %d users to set default nicknames.", len(user_ids))
    for user_id in user_ids:
        user_data = user_service.get_user(user_id)
        if not user_data:
            logger.warning("No data found for user ID %s, skipping.", user_id)
            continue
        username = user_data.get("username", "")
        if not username:
            logger.warning("User %s has no username, skipping.", user_id)
            continue
        try:
            nickname = compute_default_nickname(username, user_id)
            user_service.set(user_id, "nickname", nickname)
            logger.info("Set nickname for user %s (%s) to %s.", user_id, username, nickname)
        except Exception as e:
            logger.error("Failed to set nickname for user %s: %s", user_id, str(e))


if __name__ == "__main__":
    # Configure logging only when run as a script
    set_default_nicknames()
