""" This service implements the Christmas secret santa
service for the users designated as santa.
"""
import logging
import random
from typing import List, Tuple
from omar_bot.services.user_service import UserService
from omar_bot.config.settings import USERS_DIR


logger = logging.getLogger(__name__)


class SantaService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        self.logger = logger

    def join_santa(self, user_id: int) -> bool:
        """Adds a user to the Secret Santa event."""
        user_data = self.user_service.get_user(user_id)
        if not user_data:
            self.logger.warning("User %s not found, cannot join Secret Santa.", user_id)
            return False
        self.user_service.set(user_id, "santa", True)
        self.logger.info("User %s joined Secret Santa.", user_id)
        return True

    def leave_santa(self, user_id: int) -> bool:
        """Removes a user from the Secret Santa event."""
        user_data = self.user_service.get_user(user_id)
        if not user_data:
            self.logger.warning("User %s not found, cannot leave Secret Santa.", user_id)
            return False
        self.user_service.set(user_id, "santa", False)
        self.user_service.delete_attribute(user_id, "santa_pair")
        self.logger.info("User %s left Secret Santa.", user_id)
        return True

    def get_participants(self) -> List[int]:
        """Returns a list of user IDs participating in Secret Santa."""
        participants = [
            user_id for user_id in self.user_service.get_user_ids()
            if self.user_service.get(user_id, "santa", False)
        ]
        self.logger.debug("Secret Santa participants: %s", participants)
        return participants

    def assign_pairs(self) -> List[Tuple[int, int]]:
        """
        Assigns Secret Santa pairs randomly, ensuring no user is assigned to themselves.
        Returns a list of (giver, receiver) tuples.
        """
        participants = self.get_participants()
        if len(participants) < 2:
            self.logger.warning("Not enough participants (%s) to assign Secret Santa pairs.", len(participants))
            return []

        # Shuffle participants and create pairs
        random.shuffle(participants)
        pairs = []
        for i in range(len(participants)):
            giver = participants[i]
            receiver = participants[(i + 1) % len(participants)]  # Circular assignment
            pairs.append((giver, receiver))

        # Check for self-assignments and retry if necessary
        max_attempts = 10
        attempt = 0
        while any(giver == receiver for giver, receiver in pairs) and attempt < max_attempts:
            random.shuffle(participants)
            pairs = [(participants[i], participants[(i + 1) % len(participants)]) for i in range(len(participants))]
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

    def get_pair(self, user_id: int) -> int | None:
        """Returns the user ID of the giftee assigned to the given user."""
        return self.user_service.get(user_id, "santa_pair")

    def reset_santa(self) -> None:
        """Resets the Secret Santa event by clearing all pairings and participation."""
        for user_id in self.user_service.get_user_ids():
            self.user_service.set(user_id, "santa", False)
            self.user_service.delete_attribute(user_id, "santa_pair")
        self.logger.info("Secret Santa event reset.")
