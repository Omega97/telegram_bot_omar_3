import pytest


def test_add_user():
    arch = Architect(data_dir="test_data")
    arch.add_user(123, "Test User")
    assert 123 in arch.get_user_ids()
    assert arch.get_user_name(123) == "Test User"
