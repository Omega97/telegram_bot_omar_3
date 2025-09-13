"""
This class handles user data
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
from omar_bot.config.settings import USERS_DIR
from omar_bot.utils.helpers import get_random_emoji


def get_default_user_dict(username):
    """
    Default values for user info.
    User ID is not included, as it is used as the key
    for storing the entire dictionary (both in cache and in file).
    """
    dct = {
            "username": username,
            "emoji": get_random_emoji(),
            "gems": 0,
            "tiles_count": 0,
            "admin": False,
            "santa": False,
            "canvas": "default.csv",
            "last_place_time": None
        }
    return dct


class UserService:
    """
    Manages user data using JSON files.

    This service handles loading, saving, and modifying user information
    stored in individual JSON files within a designated directory.
    It provides methods to add, retrieve, update, and delete users.
    """
    def __init__(self, users_dir: Path = None):
        self.users_dir = users_dir or USERS_DIR
        self.users_dir.mkdir(parents=True, exist_ok=True)
        self._users = {}  # In-memory cache: {user_id: data}
        self._load_all()
        self.sorted_ids = None

    def get_user_index(self, user_id):
        if self.sorted_ids is None:
            self.sorted_ids = sorted(list(self._users))
        return self.sorted_ids.index(user_id)

    def _load_all(self) -> None:
        """Load all user JSON files into memory."""
        self._users.clear()
        for file_path in self.users_dir.glob("*.json"):
            try:
                user_id = int(file_path.stem)
                with open(file_path, "r", encoding="utf-8") as f:
                    self._users[user_id] = json.load(f)
            except (ValueError, json.JSONDecodeError) as e:
                raise RuntimeError(f"Failed to load user file: {file_path.name}") from e

    def _save_user(self, user_id: int) -> None:
        """Save a user's data to their JSON file."""
        file_path = self.users_dir / f"{user_id}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self._users[user_id], f, ensure_ascii=False, indent=2)

    def add_user(self, user_id: int, username: str) -> Dict[str, Any]:
        """Add a new user with default values."""
        if user_id in self._users:
            raise ValueError(f"User with ID {user_id} already exists.")

        # Fill the basic fields with default values
        self._users[user_id] = get_default_user_dict(username)
        self._save_user(user_id)
        self.sorted_ids = None

        return self._users[user_id]

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get full user data."""
        return self._users.get(user_id)

    def get(self, user_id: int, key: str, default: Any = None) -> Any:
        """Get a specific field for a user."""
        user = self._users.get(user_id)
        return user[key] if user and key in user else default

    def set(self, user_id: int, key: str, value: Any) -> None:
        """Set a field for a user and save to disk."""
        if user_id not in self._users:
            raise KeyError(f"User {user_id} not found.")
        self._users[user_id][key] = value
        self._save_user(user_id)

    def delete_user(self, user_id: int) -> bool:
        """Delete a user and their JSON file."""
        if user_id not in self._users:
            return False
        file_path = self.users_dir / f"{user_id}.json"
        if file_path.exists():
            file_path.unlink()  # Delete file
        del self._users[user_id]
        self.sorted_ids = None
        return True

    def get_user_ids(self) -> list:
        """Return list of all user IDs."""
        return sorted(list(self._users.keys()))

    def get_usernames(self) -> list:
        """Return list of all usernames."""
        return [self.get(uid, "username") for uid in self._users]

    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin."""
        return self.get(user_id, "admin", False)

    def get_admin_ids(self) -> list:
        """Return list of admin user IDs."""
        return [uid for uid in self._users if self.is_admin(uid)]

    def delete_attribute(self, user_id: int, key: str) -> None:
        """Delete a specific attribute for a user and save to disk."""
        if user_id not in self._users:
            raise KeyError(f"User {user_id} not found.")
        if key in self._users[user_id]:
            del self._users[user_id][key]
            self._save_user(user_id)
