"""
Test for the UserService class
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
    shutil.rmtree(temp_dir)  # Cleanup after test


@pytest.fixture
def user_service(temp_users_dir):
    """Create a UserService instance using the temp directory."""
    return UserService(users_dir=temp_users_dir)


def test_add_user(user_service):
    """Test adding a new user."""
    user = user_service.add_user(123, "Alice")
    assert user["username"] == "Alice"
    assert user["emoji"] in user["emoji"]  # valid emoji
    assert user["gems"] == 0
    assert user["admin"] is False

    # Verify file was created
    user_file = user_service.users_dir / "123.json"
    assert user_file.exists()


def test_get_user(user_service):
    """Test retrieving a user."""
    user_service.add_user(123, "Alice")
    user = user_service.get_user(123)
    assert user is not None
    assert user["username"] == "Alice"


def test_get_user_returns_none_for_missing(user_service):
    """Test that get_user returns None for non-existent user."""
    assert user_service.get_user(999) is None


def test_get_field(user_service):
    """Test getting a specific field."""
    user_service.add_user(123, "Alice")
    assert user_service.get(123, "username") == "Alice"
    assert user_service.get(123, "gems") == 0
    assert user_service.get(123, "missing", "default") == "default"


def test_set_field(user_service):
    """Test updating a user field."""
    user_service.add_user(123, "Alice")
    user_service.set(123, "gems", 10)
    assert user_service.get(123, "gems") == 10

    # Verify change was saved to disk
    user_service2 = UserService(users_dir=user_service.users_dir)
    assert user_service2.get(123, "gems") == 10


def test_delete_user(user_service):
    """Test deleting a user."""
    user_service.add_user(123, "Alice")
    user_file = user_service.users_dir / "123.json"
    assert user_file.exists()

    success = user_service.delete_user(123)
    assert success is True
    assert 123 not in user_service.get_user_ids()
    assert not user_file.exists()

    # Deleting non-existent user returns False
    assert user_service.delete_user(999) is False


def test_duplicate_user_raises_error(user_service):
    """Test that adding a duplicate user raises an error."""
    user_service.add_user(123, "Alice")
    with pytest.raises(ValueError, match="already exists"):
        user_service.add_user(123, "Bob")


def test_get_user_ids_and_usernames(user_service):
    """Test getting all user IDs and usernames."""
    user_service.add_user(123, "Alice")
    user_service.add_user(456, "Bob")

    ids = user_service.get_user_ids()
    assert sorted(ids) == [123, 456]

    names = user_service.get_usernames()
    assert "Alice" in names
    assert "Bob" in names


def test_is_admin_and_get_admin_ids(user_service):
    """Test admin-related methods."""
    user_service.add_user(123, "Alice")
    user_service.add_user(456, "Bob")

    # Initially no admins
    assert not user_service.is_admin(123)
    assert user_service.get_admin_ids() == []

    # Make Alice an admin
    user_service.set(123, "admin", True)
    assert user_service.is_admin(123)
    assert user_service.get_admin_ids() == [123]