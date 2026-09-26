""" src/omar_bot/services/santa_v2.py
This class implements the Christmas secret santa
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

    @staticmethod
    def get_help_text(_: bool = False) -> str:
        return ("🎁 **Secret Santa Control Panel**\n"
                "Select an option below to manage your groups or see your giftee.")

    def handle_who(self, user_id: int, specified_group: str = None) -> str:
        """Handles the 'who' logic and returns a formatted string for the user."""
        all_groups = self.get_user_santa_groups(user_id)

        if not all_groups:
            return "❌ You are not in any Secret Santa group.\nPlease contact an admin."

        if specified_group and specified_group not in all_groups:
            return f"❌ You are not in group `{specified_group}`."

        # If user is in exactly one group or specified one, show the result
        if specified_group or len(all_groups) == 1:
            group = specified_group or all_groups[0]
            # Internal temporary instance for that specific group
            temp_service = SantaService(self.user_service, group_name=group)
            giftee_id = temp_service.get_giftee(user_id)
            participants = temp_service.get_participant_names()

            year = datetime.now().year
            p_str = "\n".join(participants) if participants else "None"
            if giftee_id:
                name = self.user_service.get_user(giftee_id)["username"]
                return (f"🎁 Your <b>{year}</b> giftee in group <code>{group}</code> is "
                        f"<tg-spoiler><b>{name}</b></tg-spoiler>!\n\nParticipants:\n<pre>{p_str}</pre>")
            return f"🕒 No giftee assigned yet in group <code>{group}</code>.\n\nParticipants:\n<pre>{p_str}</pre>"

        # Otherwise, list available groups
        group_list = "\n".join(f"`{g}`" for g in all_groups)
        return f"🎅 You belong to **{len(all_groups)}** groups:\n{group_list}\n\nSpecify one: `/santa who [group]`"

    def handle_admin_action(self, action: str, target_id: int, group: str) -> str:
        """Validates and executes admin add/kick actions."""
        try:
            valid_g = self.validate_group_name(group)
            if not self.user_service.get_user(target_id):
                return f"❌ User `{target_id}` not found."

            if action == "add":
                self.admin_join_user_to_group(target_id, valid_g)
                return f"✅ Added `{target_id}` to `{valid_g}`."
            else:
                self.admin_kick_user_from_group(target_id, valid_g)
                return f"✅ Removed `{target_id}` from `{valid_g}`."
        except ValueError as e:
            return f"❌ {e}"

    def find_users_by_name(self, name: str) -> List[int]:
        """Return the IDs of all users whose username contains `name`
        (case-insensitive)."""
        needle = name.lower()
        matches = []
        for user_id in self.user_service.get_user_ids():
            username = self.user_service.get(user_id, "username", "")
            if needle in username.lower():
                matches.append(user_id)
        return matches

    def handle_add_by_name(self, name: str, group: str) -> str:
        """Add a user to a group by (partial, case-insensitive) name.

        If exactly one user matches, they are added and a confirmation is
        returned. Otherwise, the matching users are listed so the admin can
        retry with a more specific name.
        """
        try:
            valid_g = self.validate_group_name(group)
        except ValueError as e:
            return f"❌ {e}"

        matches = self.find_users_by_name(name)
        if not matches:
            return f"❌ No users match `{name}`."

        if len(matches) == 1:
            user_id = matches[0]
            self.admin_join_user_to_group(user_id, valid_g)
            return f"✅ Added `{self.get_user_name(user_id)}` to `{valid_g}`."

        listing = "\n".join(f"`{self.get_user_name(uid)}`" for uid in matches)
        return (f"❌ Multiple users match `{name}`. "
                f"Please be more specific and add one of:\n{listing}")

    def find_members_by_name(self, name: str, group_name: str) -> List[int]:
        """Return the IDs of members of `group_name` whose username contains
        `name` (case-insensitive)."""
        needle = name.lower()
        matches = []
        for user_id in self.user_service.get_user_ids():
            if not self.user_service.get(user_id, group_name, False):
                continue
            username = self.user_service.get(user_id, "username", "")
            if needle in username.lower():
                matches.append(user_id)
        return matches

    def handle_kick_by_name(self, name: str, group: str) -> str:
        """Kick a group member by (partial, case-insensitive) name.

        If exactly one member matches, they are removed and a confirmation is
        returned. Otherwise, the matching members are listed so the admin can
        retry with a more specific name.
        """
        try:
            valid_g = self.validate_group_name(group)
        except ValueError as e:
            return f"❌ {e}"

        matches = self.find_members_by_name(name, valid_g)
        if not matches:
            return f"❌ No members of `{valid_g}` match `{name}`."

        if len(matches) == 1:
            user_id = matches[0]
            self.admin_kick_user_from_group(user_id, valid_g)
            return f"✅ Removed `{self.get_user_name(user_id)}` from `{valid_g}`."

        listing = "\n".join(f"`{self.get_user_name(uid)}`" for uid in matches)
        return (f"❌ Multiple members match `{name}`. "
                f"Please be more specific and kick one of:\n{listing}")
