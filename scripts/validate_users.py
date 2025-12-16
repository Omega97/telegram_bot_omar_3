# scripts/validate_users.py
# todo validate data
import logging


logger = logging.getLogger(__name__)


def validate_user_data(user_id, user_data):
    required_fields = ["username", "emoji", "gems", "tiles_count"]
    for field in required_fields:
        if field not in user_data:
            logger.error(f"User {user_id} missing required field: {field}")
            return False
    # Add type validation and value constraints
    return True
