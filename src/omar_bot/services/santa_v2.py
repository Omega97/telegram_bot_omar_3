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

    def reset_santa(self) -> None:
        """Resets the Secret Santa event by clearing all pairings and participation."""
        for user_id in self.user_service.get_user_ids():
            self.user_service.set(user_id, self.group_name, False)
        self.logger.info("Secret Santa event reset.")

    def is_santa(self, user_id: int) -> bool:
        return self.user_service.get(user_id, self.group_name, False)

    def get_participants(self) -> List[int]:
        """Returns a list of user IDs participating in Secret Santa."""
        user_ids = self.user_service.get_user_ids()
        return [user_id for user_id in user_ids if self.is_santa(user_id)]

    def get_user_name(self, user_id: int) -> str:
        return self.user_service.get_user(user_id)["username"]

    def get_participant_names(self) -> List[str]:
        """Returns a list of usernames of Secret Santa participants."""
        participants = self.get_participants()
        names = [self.get_user_name(user_id) for user_id in participants]
        return names

    def get_pairings(self) -> Dict[int, int]:
        """
        Returns dict of gifter:giftee pairs.
        Assigns Secret Santa pairs pseudo-randomly using the current year and
        some secret salt as random seed.
        Ensures no user is assigned to themselves.
        Returns a dict of (gifter_id, giftee_id) tuples.
        """
        participant_ids = self.get_participants()
        year = datetime.now().year
        salt = f'{RANDOM_SALT}{year}'
        return santa_pairings(participant_ids, salt)

    def get_giftee(self, user_id: int) -> int:
        """
        Returns the user ID of the giftee assigned to the given user,
        or None if the user is not participating or no valid pairings exist.
        """
        return self.get_pairings().get(user_id, None)
