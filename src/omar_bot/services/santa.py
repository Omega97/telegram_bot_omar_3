""" This class implements the Christmas secret santa
service for the users designated as santa.
"""
import logging
import random
from typing import List, Tuple
from datetime import datetime
from omar_bot.services.user_service import UserService


logger = logging.getLogger(__name__)


class SantaService:
    """
    To determine the gift recipient, this class takes the list of all the users
    that are in that group (attribute value set to true). Then, the list is permuted
    pseudo-randomly, where the seed is the current year.

    1) get the list of the members of the santa group
    2) set random seed from current year
    3) shuffle the list
    4) the recipient of each member is the next in the list

    Every time the user uses the /santa command, the recipient is re-computed, because
    a new member might have joined the group. Also, all the other members of the santa
    group are also displayed.
    """
    def __init__(self, user_service: UserService, key_name: str = "santa"):
        """
        :param user_service: UserService instance to manage user data
        :param key_name: name of the attribute (change this to handle a different santa group)
        """
        self.user_service = user_service
        self.logger = logger
        self.key_name = key_name

    def join_santa(self, user_id: int) -> bool:
        """Adds a user to the Secret Santa event."""
        user_data = self.user_service.get_user(user_id)
        if not user_data:
            self.logger.warning("User %s not found, cannot join Secret Santa.", user_id)
            return False
        self.user_service.set(user_id, self.key_name, True)
        self.user_service.delete_attribute(user_id, "santa_pair")  # Clear previous pair
        self.logger.info("User %s joined Secret Santa.", user_id)
        return True

    def leave_santa(self, user_id: int) -> bool:
        """Removes a user from the Secret Santa event."""
        user_data = self.user_service.get_user(user_id)
        if not user_data:
            self.logger.warning("User %s not found, cannot leave Secret Santa.", user_id)
            return False
        self.user_service.set(user_id, self.key_name, False)
        self.user_service.delete_attribute(user_id, "santa_pair")
        self.logger.info("User %s left Secret Santa.", user_id)
        return True

    def get_participants(self) -> List[int]:
        """Returns a list of user IDs participating in Secret Santa."""
        participants = [
            user_id for user_id in self.user_service.get_user_ids()
            if self.user_service.get(user_id, self.key_name, False)
        ]
        self.logger.debug("Secret Santa participants: %s", participants)
        return participants

    def get_participant_names(self) -> List[str]:
        """Returns a list of usernames of Secret Santa participants."""
        participants = self.get_participants()
        names = [self.user_service.get_user(user_id)["username"] for user_id in participants]
        self.logger.debug("Secret Santa participant names: %s", names)
        return names

    def assign_pairs(self) -> List[Tuple[int, int]]:
        """
        Assigns Secret Santa pairs randomly using the current year as the seed.
        Ensures no user is assigned to themselves.
        Returns a list of (giver, receiver) tuples.
        """
        participants = self.get_participants()
        if len(participants) < 2:
            self.logger.warning("Not enough participants (%s) to assign Secret Santa pairs.",
                                len(participants))
            return []

        # Set random seed based on current year
        current_year = datetime.now().year
        random.seed(current_year)
        self.logger.debug("Set random seed to current year: %s", current_year)

        # Shuffle participants and create pairs
        participants_shuffled = participants.copy()
        random.shuffle(participants_shuffled)
        n = len(participants_shuffled)
        pairs = []
        for i in range(n):
            giver = participants_shuffled[i]
            receiver = participants_shuffled[(i + 1) % n]  # Circular assignment
            pairs.append((giver, receiver))

        # Check for self-assignments and retry if necessary
        max_attempts = 10
        attempt = 0
        while any(giver == receiver for giver, receiver in pairs) and attempt < max_attempts:
            random.seed(current_year)  # Reset seed for consistency
            random.shuffle(participants_shuffled)
            pairs = [(participants_shuffled[i], participants_shuffled[(i + 1) % n]) for i in range(n)]
            attempt += 1

        if any(giver == receiver for giver, receiver in pairs):
            self.logger.error("Failed to assign valid Secret Santa pairs after %s attempts.", max_attempts)
            return []

        # Save pairs to user data
        for giver, receiver in pairs:
            self.user_service.set(giver, "santa_pair", receiver)
            self.logger.info("Assigned %s to give to %s.", giver, receiver)

        self.logger.info("Secret Santa pairs assigned: %s", pairs)
        return pairs

    def get_pair(self, user_id: int) -> Tuple[int | None, List[str]]:
        """
        Returns the user ID of the giftee assigned to the given user and the list of participant usernames.
        Recomputes pairs dynamically to account for new participants.
        """
        if not self.user_service.get_user(user_id):
            self.logger.warning("User %s not found, cannot get Secret Santa pair.", user_id)
            return None, []

        # Recompute pairs to ensure up-to-date assignments
        pairs = self.assign_pairs()
        if not pairs:
            self.logger.warning("No valid Secret Santa pairs available for user %s.", user_id)
            return None, self.get_participant_names()

        # Find the user's giftee
        giftee_id = None
        for giver, receiver in pairs:
            if giver == user_id:
                giftee_id = receiver
                break

        return giftee_id, self.get_participant_names()

    def reset_santa(self) -> None:
        """Resets the Secret Santa event by clearing all pairings and participation."""
        for user_id in self.user_service.get_user_ids():
            self.user_service.set(user_id, self.key_name, False)
            self.user_service.delete_attribute(user_id, "santa_pair")
        self.logger.info("Secret Santa event reset.")
