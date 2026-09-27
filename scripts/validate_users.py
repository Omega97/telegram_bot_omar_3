# scripts/validate_users.py
"""Validate the user records stored in the JSON database.

Run as a script to check every user for missing required fields and for
incorrectly typed or out-of-range values:

    python scripts/validate_users.py
"""
import sys
from pathlib import Path
from typing import Any, Dict, List

from omar_bot.config.settings import USERS_DIR
from omar_bot.services.user_service import UserService


REQUIRED_FIELDS = ("username", "emoji", "gems", "tiles_count")


def _is_str(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


# Validators for known fields. Unknown/extra fields are ignored.
FIELD_VALIDATORS = {
    "username": _is_str,
    "emoji": _is_str,
    "nickname": _is_str,
    "canvas": _is_str,
    "gems": _is_non_negative_int,
    "tiles_count": _is_non_negative_int,
    "gold": _is_non_negative_int,
    "santa": lambda v: isinstance(v, bool),
    "admin": lambda v: isinstance(v, bool),
    "last_place_time": lambda v: v is None or isinstance(v, (int, float)),
}


def validate_user_data(user_id: int, user_data: Dict[str, Any]) -> List[str]:
    """Return a list of validation errors for a user (empty if valid)."""
    errors = []

    for field in REQUIRED_FIELDS:
        if field not in user_data:
            errors.append(f"missing required field '{field}'")

    for field, value in user_data.items():
        validator = FIELD_VALIDATORS.get(field)
        if validator is not None and not validator(value):
            errors.append(f"invalid value for '{field}': {value!r}")

    return errors


def main() -> int:
    if not USERS_DIR.exists():
        print(f"[ERROR] Directory not found: {USERS_DIR}")
        return 1

    service = UserService(users_dir=Path(USERS_DIR))
    user_ids = service.get_user_ids()
    if not user_ids:
        print("No users found.")
        return 0

    print(f"\nValidating {len(user_ids)} user(s)...\n")

    invalid_count = 0
    for user_id in user_ids:
        errors = validate_user_data(user_id, service.get_user(user_id))
        if errors:
            invalid_count += 1
            print(f"[FAIL] User {user_id}: {', '.join(errors)}")
        else:
            print(f"[OK]   User {user_id}")

    print()
    if invalid_count:
        print(f"[FAIL] {invalid_count}/{len(user_ids)} users have invalid data.")
        return 1

    print(f"[OK] All {len(user_ids)} users are valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
