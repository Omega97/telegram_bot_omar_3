import pytest
import logging
# 1. Import the handlers package FIRST to trigger all @register_command decorators
# This runs the logic in src/omar_bot/handlers/__init__.py
from omar_bot import handlers

# 2. Import the dictionary using the EXACT SAME PATH style used in your handlers
from omar_bot.command_registry import COMMAND_HANDLERS


def test_command_registry_population():
    """
    Test that ensures all commands are successfully registered
    in the global COMMAND_HANDLERS dictionary.
    """
    # Count the number of registered commands
    count = len(COMMAND_HANDLERS)

    print(f"\n[TEST] Found {count} commands in registry.")

    # Assert that we have at least some core commands registered
    assert count > 0, "COMMAND_HANDLERS is empty! Check your import paths."

    # Assert that specific known commands exist
    assert "start" in COMMAND_HANDLERS
    assert "stop" in COMMAND_HANDLERS

    # Log the full list of commands for debugging
    command_names = sorted(COMMAND_HANDLERS.keys())
    logging.info(f"Registered commands: {', '.join(command_names)}")


def test_command_metadata_structure():
    """
    Test that each registered command has the required metadata.
    """
    for name, data in COMMAND_HANDLERS.items():
        assert "handler" in data, f"Command '{name}' is missing a handler function."
        assert "description" in data, f"Command '{name}' is missing a description."
        assert "admin_only" in data, f"Command '{name}' is missing the admin_only flag."

        # Ensure description was correctly extracted from docstrings
        assert isinstance(data["description"], str)
