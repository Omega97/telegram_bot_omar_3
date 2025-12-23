from omar_bot.command_registry import setup_commands


def test_command_registry_population():
    # Explicitly call the setup
    commands = setup_commands()

    count = len(commands)
    assert count > 0
    assert "start" in commands
    print(f"\n[TEST] Successfully loaded {count} commands.")
