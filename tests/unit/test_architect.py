"""
Basic sanity test for user management.
"""
import pytest
from pathlib import Path
import tempfile
import shutil
from omar_bot.services.user_service import UserService


@pytest.fixture
def temp_users_dir():
    """Create a temporary directory for user data."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)


def test_add_user(temp_users_dir):
    service = UserService(users_dir=temp_users_dir)
    service.add_user(123, "Test User")
    assert 123 in service.get_user_ids()
    assert service.get_user(123)["username"] == "Test User"
