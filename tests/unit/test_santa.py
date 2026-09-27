"""
Tests for the Secret Santa pairing logic.
"""
import pytest
from pathlib import Path
import tempfile
import shutil

from omar_bot.services.santa_v2 import SantaService, santa_pairings
from omar_bot.services.user_service import UserService


@pytest.fixture
def temp_users_dir():
    """Create a temporary directory for user data."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture
def santa_service(temp_users_dir, monkeypatch):
    """A SantaService backed by temporary users with a deterministic salt."""
    user_service = UserService(users_dir=temp_users_dir)
    for uid, name in [(1, "Alice"), (2, "Bob"), (3, "Charlie"), (4, "Diana")]:
        user_service.add_user(uid, name)
        user_service.set(uid, "santa", True)

    service = SantaService(user_service, group_name="santa")
    monkeypatch.setattr(service, "random_salt", "test-salt")
    return service


def _assert_valid_pairings(pairings, players):
    """Every player gifts once, receives once, and (with >1 players) never gifts itself."""
    assert set(pairings) == set(players)
    assert set(pairings.values()) == set(players)
    if len(players) > 1:
        for gifter, giftee in pairings.items():
            assert gifter != giftee


def test_santa_pairings_is_valid():
    players = [1, 2, 3, 4]
    _assert_valid_pairings(santa_pairings(players, "salt"), players)


def test_santa_pairings_deterministic():
    players = [1, 2, 3, 4]
    assert santa_pairings(players, "salt") == santa_pairings(players, "salt")


def test_get_pairings_uses_participants_only(santa_service):
    pairings = santa_service.get_pairings(year=2025)
    participants = santa_service.get_participants()
    assert set(participants) == {1, 2, 3, 4}
    _assert_valid_pairings(pairings, participants)


def test_get_pairings_deterministic_per_year(santa_service):
    assert santa_service.get_pairings(year=2025) == santa_service.get_pairings(year=2025)


def test_get_pairings_incorporates_year(santa_service):
    participants = santa_service.get_participants()
    assert santa_service.get_pairings(year=2025) == santa_pairings(participants, "test-salt2025")
