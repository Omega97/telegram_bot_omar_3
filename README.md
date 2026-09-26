# Telegram Bot v3
by Omar Fait


## ✅ Implemented Features

- `.gitignore` and `requirements.txt`
- Local environment setup with `.env` file
- Environment variable handling in `config/settings.py`
- Unit tests (in `tests/unit/`)
- User data migration to JSON database (`data/PRIVATE/users/`)
- `UserService` class for user data management
- User editor console for viewing/editing user info (`scripts/user_editor_console.py`)
- Core bot structure (`src/omar_bot/bot.py`)
- Command handler registry (`src/omar_bot/handlers/user_commands.py`)
- Comprehensive logging setup
- Gentle termination for `/stop` command
- Commands get automatically registered with the @register_command decorator

---

### User Commands

  - `/start` – Welcome message and user registration
  - `/help` – Context-aware help (shows admin commands only to admins)
  - `/users` – List all users with emojis and nicknames
  - `/gems` – Leaderboard of users with gems (sorted by count)
  - `/gold` – List users with gold amounts
  - `/myprofile` – Show your complete profile information
  - `/santa` – Secret Santa participation and assignment system
    - `/santa who` – See your assigned giftee
    - `/santa status` – Check participation status
    - `/santa add` – Add user to a santa group (admin-only)
    - `/santa kick` – Kick member from a santa group (admin-only)
    - `/santa reset` – Reset event (admin-only)
  - `/place` – Canvas/tile placement system
    - View current canvas
    - Place tiles at coordinates `[x] [y]`
    - Remove your own tiles by placing on them again
    - Earn gems and track tile count
    - `/roll` – roll a dice
---

### Admin Commands

- **Admin Commands**:
  - `/stop` – Graceful bot shutdown
  - `/set_canvas [user] [canvas]` – Change user's canvas
  - `/reset_canvas [canvas]` – Clear all tiles from canvas
  - `/delete_canvas [canvas]` – Delete canvas file
  - `/set_emoji` – Set user emoji manually

---

## ❌ Not Implemented (Todo)

### User Commands:
- `/gamble` – Gambling system
- `/leaderboard` – Comprehensive leaderboard (gems/tiles combined)

---

### Admin Commands:
- `/get_ids` – Get user IDs
- `/get_info` – Get detailed user information
- `/give_gems` – Award gems to users
- `/canvas_names` – List available canvases
- `/password` – Password management system

---

## 🖥️ Running the User Editor Console

The user editor console (`scripts/user_editor_console.py`) lets you view and edit user data from the terminal.

1. Move to the project root:

```
cd C:\Users\monfalcone\PycharmProjects\telegram_bot_omar_3
```

2. Activate the virtual environment:

   - Windows:
```
.venv\Scripts\activate
```
   - macOS / Linux:
```
source .venv/bin/activate
```

3. (First time only) Install the package in editable mode so the `omar_bot` imports resolve:

```
pip install -e .
```

4. Launch the console:

```
python scripts\user_editor_console.py
```

   Once running, type `help` (or `?`) to see the list of available commands, and `quit` to exit.

---

