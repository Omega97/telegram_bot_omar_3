""" This class implements the Christmas secret santa
service for the users designated as santa.
"""
import logging
from typing import List, Dict
from datetime import datetime
from omar_bot.services.user_service import UserService
from omar_bot.config.settings import RANDOM_SALT
from omar_bot.utils.utils import sha256_hash


logger = logging.getLogger(__name__)


def santa_pairings(players: List[int], salt: str) -> Dict[int, int]:
    """
    Deterministically assign Secret-Santa pairs. Guaranteed that noone has
    to gift itself (with more than one player).

    Build a reproducible order: sort by SHA-256(name + salt)
    Circular pairing: each person gives to the next in the list

    Usage:
        Use 'get_pairings' to get all the pairings.
        Use 'get_giftee' to get the giftees of a given user.
    """
    ordered = sorted(players, key=lambda n: sha256_hash(f"{n}{salt}"))
    return {ordered[i]: ordered[(i + 1) % len(ordered)] for i in range(len(ordered))}


class SantaService:
    """
    To determine the gift recipient, this class takes the list of all the users
    that are in that group (attribute value set to true). Then, the list is permuted
    pseudo-randomly, where the seed is the current year.

    Every time the user uses the /santa command, the recipient is re-computed, because
    a new member might have joined the group. Also, all the other members of the santa
    group are also displayed.
    """
    def __init__(self, user_service: UserService, group_name: str = "santa"):
        """
        :param user_service: UserService instance to manage user data
        :param group_name: name of the attribute (change this to handle a different santa group)
        """
        self.user_service = user_service
        self.logger = logger
        self.group_name = group_name
        self.random_salt = RANDOM_SALT

    def join_santa(self, user_id: int) -> bool:
        """
        Adds a user to the Secret Santa event by setting
        the 'self.group_name' tag of the user to True.
        """
        user_data = self.user_service.get_user(user_id)
        if not user_data:
            self.logger.warning("User %s not found, cannot join Secret Santa.", user_id)
            return False

        # Set 'self.group_name' tag to True to join santa group
        self.user_service.set(user_id, self.group_name, True)
        self.logger.info("User %s joined Secret Santa.", user_id)
        return True

    def leave_santa(self, user_id: int) -> bool:
        """Removes a user from the Secret Santa event."""
        user_data = self.user_service.get_user(user_id)
        if not user_data:
            self.logger.warning("User %s not found, cannot leave Secret Santa.", user_id)
            return False
        self.user_service.set(user_id, self.group_name, False)
        self.logger.info("User %s left Secret Santa.", user_id)
        return True

    def is_santa(self, user_id: int) -> bool:
        return self.user_service.get(user_id, self.group_name, False)

    def get_participants(self) -> List[int]:
        """Returns a list of user IDs participating in Secret Santa."""
        user_ids = self.user_service.get_user_ids()
        return [user_id for user_id in user_ids if self.is_santa(user_id)]

    def get_user_name(self, user_id: int) -> str:
        user_data = self.user_service.get_user(user_id)
        return user_data["username"] if user_data else "Unknown User"

    def get_participant_names(self) -> List[str]:
        """Returns a list of usernames of Secret Santa participants."""
        participants = self.get_participants()
        names = [self.get_user_name(user_id) for user_id in participants]
        return names

    def get_pairings(self, year: int | None = None) -> Dict[int, int]:
        """
        Returns dict of gifter:giftee pairs.
        Assigns Secret Santa pairs pseudo-randomly using the current year and
        some secret salt as random seed.
        Ensures no user is assigned to themselves.
        Returns a dict of (gifter_id, giftee_id) tuples.
        """
        participant_ids = self.get_participants()
        if year is None:
            year = datetime.now().year
        salt = f'{self.random_salt}{year}'
        return santa_pairings(participant_ids, salt)

    def get_giftee(self, user_id: int, year: int | None = None) -> int | None:
        """
        Returns the user ID of the giftee assigned to the given user,
        or None if the user is not participating or no valid pairings exist.
        """
        return self.get_pairings(year=year).get(user_id, None)

    @staticmethod
    def validate_group_name(name: str) -> str:
        name = name.strip().lower()
        if not name.startswith("santa"):
            raise ValueError("Group name must start with 'santa'")
        return name

    def admin_join_user_to_group(self, user_id: int, group_name: str) -> None:
        self.user_service.set(user_id, group_name, True)

    def admin_kick_user_from_group(self, user_id: int, group_name: str) -> None:
        self.user_service.set(user_id, group_name, False)

    def reset_santa(self, group_name: str | None = None) -> List[str]:
        """
        Reset one or all Santa groups.

        If group_name is None: returns list of all existing santa groups (no deletion).
        If group_name is provided: deletes that specific group from all users.

        Returns:
            - List of group names if group_name is None
            - Empty list on success if group_name is provided
            - List with error message on failure
        """
        if group_name is None:
            # Return list of all santa groups
            keys = set()
            for uid in self.user_service.get_user_ids():
                user_data = self.user_service.get_user(uid)
                for key in user_data:
                    if key.startswith("santa"):
                        keys.add(key)
            return sorted(keys)
        else:
            # Delete specific group
            if not group_name.startswith("santa"):
                return [f"Invalid group name: {group_name}. Must start with 'santa'"]
            for uid in self.user_service.get_user_ids():
                user_data = self.user_service.get_user(uid)
                if group_name in user_data:
                    self.user_service.delete_attribute(uid, group_name)
            return []  # success

    def get_user_santa_groups(self, user_id: int) -> List[str]:
        """Returns a sorted list of all Santa group names for which the user's value is truthy."""
        user_data = self.user_service.get_user(user_id)
        if not user_data:
            return []
        return sorted([
            key for key, value in user_data.items()
            if key.startswith("santa") and value
        ])

    def get_help_text(self, admin: bool = False) -> str:
        public_lines = [
            "🎅 Secret Santa Commands:",
            "`/santa who` - See your assigned giftee and participants.",
            "`/santa groups` - List the Santa groups you belong to."
        ]

        if admin:
            public_lines.extend([
                "",
                "✨ **Admin-only**:",
                "`/santa join [user_id] [group]` - Add user to a Santa group (e.g., `santa_xmas2025`).",
                "`/santa kick [user_id] [group]` - Remove user from a group.",
                "`/santa reset` - List all Secret Santa groups.",
                "`/santa reset [group]` - Delete a specific group."
            ])

        return "\n".join(public_lines)
