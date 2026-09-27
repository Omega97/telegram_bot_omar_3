"""
Tests for the user data validation logic.
"""
from scripts.validate_users import validate_user_data


def test_valid_user():
    user = {
        "username": "Alice",
        "emoji": "🦊",
        "gems": 5,
        "tiles_count": 2,
        "gold": 1,
        "santa": True,
        "canvas": "default",
        "last_place_time": None,
    }
    assert validate_user_data(123, user) == []


def test_missing_required_field():
    user = {"username": "Alice", "emoji": "🦊", "gems": 0}
    errors = validate_user_data(123, user)
    assert "missing required field 'tiles_count'" in errors


def test_invalid_type_and_range():
    user = {
        "username": "",
        "emoji": "🦊",
        "gems": -1,
        "tiles_count": "many",
    }
    errors = validate_user_data(123, user)
    assert any("'username'" in e for e in errors)
    assert any("'gems'" in e for e in errors)
    assert any("'tiles_count'" in e for e in errors)


def test_boolean_rejected_for_int_field():
    user = {"username": "Alice", "emoji": "🦊", "gems": True, "tiles_count": 0}
    errors = validate_user_data(123, user)
    assert any("'gems'" in e for e in errors)
