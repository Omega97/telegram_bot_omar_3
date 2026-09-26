# TODO

A running list of known issues and improvements. Organized by category and priority.

## 🐛 Bugs

- [x] **`/start` does not actually register users.** `start()` in `user_commands.py` only sends a welcome message — it never calls `UserService.add_user()`. Many commands (`/myprofile`, `/santa`, `/place`) reply "register with /start", but registration never happens. Either register in `/start` or drop the registration requirement.
- [x] **`ADMIN_IDS` from `.env` is never used.** Admin status is determined solely by the `admin` flag in each user's JSON. `ADMIN_IDS` is parsed and required by `env_sanity_check()`, but ignored by `UserService.is_admin()`. Decide on a single source of truth.
- [x] **`myprofile` default canvas name is inconsistent.** `get_default_user_dict()` uses `"default.csv"`, but `PlaceService.get_place_response()`/`attempt_place_tile()` fall back to `"default"` (no `.csv`). Same user can hit different canvases depending on the code path.
- [x] **`error_handler` is defined but never registered.** `bot.py` defines `error_handler()` but never calls `application.add_error_handler(...)`, so exceptions are logged by the fallback "No error handlers are registered" path (visible in `ai-feed.txt`).
- [x] **`tests/unit/test_architect.py` references a non-existent `Architect` class.** No import, no definition → the test always errors with `NameError`.
- [x] **Canvas dimensions are swapped (transposed).** `empty_canvas(rows, cols)` builds `rows` rows × `cols` columns, but:
  - `PlaceService.create_canvas()` calls `empty_canvas(width, height)` → width/height reversed.
  - `PlaceService.reset_canvas()` calls `empty_canvas(len(grid[0]), len(grid))` → also reversed.
  The `scripts/transpose_canvases.py` workaround exists because of this. Fix the argument order (`empty_canvas(height, width)` and `empty_canvas(len(grid), len(grid[0]))`).
- [x] **`PlaceService.place_tile()` returns `True` on a load failure.** The `if grid is None: return True, "Cannot load the canvas"` branch reports success with an error message. Should return `False`.

## ⚠️ Edge cases / Potential bugs

- [ ] **Removing your own tile never decrements `tiles_count`/`gems`.** `place_tile()` removes the tile but leaves counts unchanged, so `tiles_count` drifts from the number of actually-placed tiles.
- [ ] **`place_tile()` silently overwrites another user's tile.** There is no ownership check beyond "is it mine or not"; placing on someone else's tile replaces it. Confirm this is intended.
- [ ] **`/start` uses `user.full_name.split(" ")[0]`** — crashes or mis-names users with empty/`None` full names.
- [ ] **`get_user_name()` / `handle_who()` use `user_data["username"]`** (direct indexing). Legacy/missing keys would raise `KeyError` (same class of bug already fixed in `myprofile`). Prefer `.get("username", "Unknown")`.
- [ ] **`UserService.get_user_index()` calls `list.index(user_id)`**, which raises `ValueError` for unknown IDs and relies on `sorted_ids` staying in sync.
- [ ] **`santa_pairings()` with a single participant** assigns the user to themselves (self-gift). Docstring acknowledges it, but it's worth guarding explicitly.
- [ ] **`ADMIN_IDS` parsing breaks on spaces** (`int(" 123")`), despite the template saying "no spaces". Strip each entry.
- [ ] **`convert_string()` in `utils.py` has a stray `print(s)`** debug statement.
- [ ] **`check_users.py` sorts by `int(f.stem)`** and will crash if a non-numeric file appears in `USERS_DIR`.

## 🎨 UI / UX improvements

- [ ] **`/users` docstring says it shows IDs, but it only shows emoji + nickname.** Either show IDs or fix the description.
- [ ] **`/gems` docstring mentions IDs but doesn't display them.**
- [ ] **`/draw` sorts the drawn tokens (`sorted(...)`), which destroys the random draw order** and always renders the bag as "whites then blacks". Consider preserving shuffle order.
- [ ] **`LoggingBot` only logs `send_message`**, not `edit_message_text` (used by the Santa inline buttons).
- [ ] **Secret Santa help text is identical for admins and non-admins** (`get_help_text` ignores the `is_admin` flag); the extra admin button is added in the handler instead.
- [ ] **`/help` output can overflow Telegram's message limit** once many commands are registered — consider pagination.
- [ ] **`/place` view uses `⏹️`/number emoji as coordinate labels**, which are ambiguous for canvases wider than 10 columns (digits repeat). Add a clearer coordinate legend.

## ♻️ Refactors / code quality

- [ ] **`UserService.set()` writes to disk on every call.** `place_tile()` triggers 3 separate disk writes (`last_place_time`, `tiles_count`, `gems`). Batch updates or add a `set_many()`.
- [ ] **`convert_string()` is duplicated logic** with `convert_value()`; consolidate.
- [ ] **`compute_default_nickname()` is duplicated** in `user_service.py` and `scripts/set_default_nickname.py`. Import one from the other.
- [ ] **`echo`/`process_message()` is a pure echo** with a `#todo implement core bot` marker — implement real message processing or remove the TODO.
- [ ] **`ADMIN_IDS` vs per-user `admin` flag** should be unified (see Bugs) to avoid two competing admin systems.
- [ ] **`register_command` wraps admin commands with a duplicate `UserService` instantiation per call** — could share a single service/connection.

## 🧪 Tests

- [ ] **`test_santa.py` depends on the real `USERS_DIR` and hardcoded user IDs** (`_CORRECT_PAIRINGS`). Use a temp dir + fixture so the test is hermetic.
- [ ] **`test_architect.py` is broken** (missing `Architect` — see Bugs).
- [ ] **No tests cover the canvas dimension bug, `/draw`, `/roll`, or `RecentTracker`** filtering logic.
- [ ] **`validate_users.py` is a stub** (`# todo validate data`) — implement actual field validation and wire it into startup or a script.

## 📋 Misc

- [ ] test santa groups
- [ ] **`env_sanity_check()` typo:** "Sanity chack passed" → "Sanity check passed".
- [ ] **README `/roll` bullet is misaligned** under the `/place` section.
