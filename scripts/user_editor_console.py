"""
This console can quickly display and edit user info.
"""
from omar_bot.config.settings import USERS_DIR
from omar_bot.services.user_service import UserService
from omar_bot.utils.utils import convert_value


class UserEditor:
    """Console-based user management interface"""

    def __init__(self):
        self.service = UserService(users_dir=USERS_DIR)
        self.selected_users = []  # List of selected user IDs
        self.commands = dict()

        self.structure = (
            (self.cmd_help, ("help", "h", "?")),
            (self.cmd_list, ("list", "ls")),
            (self.cmd_find_user, ("find_user", "find", "fu")),
            (self.cmd_select, ("select", "sel", "s")),
            (self.cmd_select_all, ("select_all", "sa")),
            (self.cmd_deselect, ("deselect", "desel", "d")),
            (self.cmd_deselect_all, ("deselect_all", "da")),
            (self.cmd_show_selected_info, ("selected_info", "info_selected", "i")),
            (self.cmd_add_attribute, ("add_attr", "aa")),
            (self.cmd_set_attribute, ("set_attr", "set")),
            (self.cmd_get_attribute, ("get_value", "get_attr", "show", "get")),
            (self.cmd_remove_attribute, ("remove_attr", "ra")),
            (self.cmd_add_user, ("add_user", "au")),
            (self.cmd_remove_user, ("remove_user",)),
            (self.cmd_quit, ("quit", "q", "exit")),
        )

        self._init_commands()

    def _init_commands(self):
        for method, names in self.structure:
            for name in names:
                self._add_command(method, name)

    def _add_command(self, method, keyword: str):
        assert keyword
        assert keyword not in self.commands, keyword
        self.commands[keyword] = method

    def get_user_index(self, user_id):
        return self.service.get_user_index(user_id)

    def run(self):
        """Main loop for the editor"""
        print()
        print("=" * 50)
        print(" " * 12 + "USER MANAGEMENT CONSOLE")
        print("=" * 50)
        print("Type 'help' or '?' for available commands")
        print()

        while True:
            try:
                command_input = input("\n> ").strip()
                if not command_input:
                    continue

                # Handle command with arguments
                parts = command_input.split(maxsplit=1)
                cmd_name = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""

                if cmd_name in self.commands:
                    # Allow cmd_quit to return False to stop the loop
                    if self.commands[cmd_name](args) is False:
                        break
                else:
                    print(f"❌ Unknown command: {cmd_name}")
                    print("Type 'help' for available commands")
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")
            except Exception as e:
                print(f"⚠️ Error: {str(e)}")

    @staticmethod
    def cmd_help(*_):
        """Show available commands"""
        print("\n AVAILABLE COMMANDS:")
        print("  help, h, ?          - Show this help message")
        print("  list, ls, l         - List all users OR selected users")
        print("  select, sel, s      - Select user(s) by index or ID")
        print("  select_all, sa      - Select all users")
        print("  info, i             - Show all info about selected users")
        print("  deselect, desel, d  - Remove user from selection")
        print("  deselect_all, da    - Remove all users from selection")
        print("  find_user, fu       - Find user by name")
        print("  add_attr, aa        - Add attribute to users without it")
        print("  set_attr, set       - Set attribute for selected users")
        print("  show, get           - Show values of given feature OR show users by value")
        print("  remove_attr, ra     - Remove attribute from selected users")
        print("  add_user, au        - Add a new user")
        print("  remove_user         - Remove a user")
        print("  quit, q, exit       - Exit the program")

    def parse_selection(self, selection_str):
        """Parse selection string into user IDs"""
        user_ids = self.service.get_user_ids()
        selected = []
        selection_str = selection_str.replace(",", " ")
        parts = [s.strip() for s in selection_str.split(" ")]
        parts = [s for s in parts if s]

        # Handle [tag, value] case
        if len(parts) == 2:
            if type(convert_value(parts[0])) is str:
                return self.find_users_by_feature(selection_str)

        for part in parts:

            # Handle range (e.g., "2-5")
            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    for i in range(start, end + 1):
                        if 0 <= i < len(user_ids):
                            selected.append(user_ids[i])
                except ValueError:
                    print(f"❌ Invalid range format: {part}")

            # Handle single index
            elif part.isdigit():
                idx = int(part)
                if 0 <= idx < len(user_ids):
                    selected.append(user_ids[idx])
                else:
                    print(f"❌ Index {idx} out of range (0-{len(user_ids) - 1})")

            # Handle user ID
            else:
                try:
                    user_id = int(part)
                    if user_id in user_ids:
                        selected.append(user_id)
                    else:
                        print(f"❌ User ID {user_id} not found")
                except ValueError:
                    print(f"❌ Invalid selection: {part}")

        return selected

    def add_selection(self, user_ids_to_add):
        """
        Adds a list of user IDs to the selection, provides feedback,
        and skips any duplicates.
        """
        for user_id in user_ids_to_add:
            if user_id not in self.selected_users:
                self.selected_users.append(user_id)
                username = self.service.get(user_id, 'username')
                print(f"✅ Selected: {user_id} {username}")

    def cmd_find_user(self, args=""):
        """
        Find and list users by a case-insensitive username substring.
        """
        if not args:
            print("❓ Usage: find_user [substring]")
            print("   Example: find_user Alice")
            return

        search_query = args.lower().strip()
        user_ids = self.service.get_user_ids()

        found_users = []
        for uid in user_ids:
            username = self.service.get(uid, 'username')
            if username and search_query in username.lower():
                found_users.append(uid)

        if not found_users:
            print(f"❌ No users found with '{args}' in their username.")
            return

        print(f"\n🔎 Found {len(found_users)} users matching '{args}':")
        for uid in user_ids:
            if uid in found_users:
                i = self.get_user_index(uid)
                emoji = self.service.get(uid, 'emoji')
                username = self.service.get(uid, 'username')
                print(f"{i:3}) {uid:11} {emoji} {username}")

    def cmd_select(self, args=""):
        """Select user(s) by index or ID"""
        if not args:
            print("❓ Usage: select [index(es) or ID(s)]")
            print("❓ Usage: select [tag] [value]")
            print("   Examples:")
            print("   select 0 1 2")
            print("   select 2-5")
            print("   select 123456789")
            print("   select santa True")
            return

        new_selection = self.parse_selection(args)
        if not new_selection:
            return

        self.add_selection(new_selection)

        print(f"\n📌 Total selected: {len(self.selected_users)}")

    def cmd_select_all(self, args=""):
        """Select all users"""
        all_user_ids = self.service.get_user_ids()
        if not all_user_ids:
            print("❌ No users found to select")
            return

        self.add_selection(all_user_ids)

        print(f"\n📌 Total selected: {len(self.selected_users)}")

    def cmd_deselect(self, args=""):
        """Remove user from selection"""
        if not self.selected_users:
            print("❌ No users selected")
            return

        if not args:
            print("❓ Usage: deselect [index(es)]")
            print("   Examples:")
            print("   deselect 2")
            return

        # Parse indices to remove (these are indices in the SELECTION list, not user IDs)
        to_remove = []
        for part in args.split(','):
            part = part.strip()
            if not part:
                continue

            if '-' in part:
                try:
                    start, end = map(int, part.split('-'))
                    for i in range(start, end + 1):
                        if 0 <= i < len(self.selected_users):
                            to_remove.append(i)
                except ValueError:
                    print(f"❌ Invalid range format: {part}")
            else:
                try:
                    idx = int(part)
                    if 0 <= idx < len(self.selected_users):
                        to_remove.append(idx)
                    else:
                        print(f"❌ Index {idx} out of range (0-{len(self.selected_users) - 1})")
                except ValueError:
                    print(f"❌ Invalid index: {part}")

        # Remove selected indices (in reverse order to avoid index shifting)
        for idx in sorted(to_remove, reverse=True):
            user_id = self.selected_users[idx]
            print(f"❌ Deselected: {user_id} {self.service.get(user_id, 'username')}")
            del self.selected_users[idx]

        print(f"\n📌 Remaining selected: {len(self.selected_users)}")

    def cmd_deselect_all(self, args=""):
        """Remove all users from selection"""
        if not self.selected_users:
            print("❌ No users selected")
            return

        count = len(self.selected_users)
        self.selected_users.clear()
        print(f"☑️ Deselected all {count} users")

    def cmd_list(self, args=""):
        """Show currently selected users"""
        users = self.selected_users
        if not self.selected_users:
            users = self.service.get_user_ids()

        print(f"\n📌 {len(self.selected_users)} users selected:")
        for uid in users:
            i = self.get_user_index(uid)
            emoji = self.service.get(uid, 'emoji')
            username = self.service.get(uid, 'username')
            print(f"{i:3}) {uid:11} {emoji} {username}")

    def cmd_show_selected_info(self, args=""):
        """Show all information about selected users"""
        if not self.selected_users:
            print("❌ No users selected")
            return

        print(f"\n📋 INFO FOR {len(self.selected_users)} SELECTED USER(S):")
        print("=" * 60)

        for user_id in self.selected_users:
            try:
                user_data = self.service.get_user(user_id)
                if not user_data:
                    print(f"⚠️  User {user_id}: No data found")
                    continue

                # Get username and emoji for header
                username = user_data.get('username', 'Unknown')
                emoji = user_data.get('emoji', '👤')

                print(f"{user_id:11} {emoji} {username}")
                print("-" * 40)

                # Sort keys for consistent display (put important ones first)
                priority_keys = ['username', 'emoji', 'admin', 'santa', 'gems', 'tiles_count', 'canvas',
                                 'last_place_time']
                other_keys = [k for k in user_data.keys() if k not in priority_keys]
                sorted_keys = priority_keys + sorted(other_keys)

                # Display all attributes
                for key in sorted_keys:
                    if key in user_data:
                        value = user_data[key]
                        print(f"  {key:15} : {repr(value)}")

                print()

            except Exception as e:
                print(f"❌ Error loading data for user {user_id}: {e}\n")

    def cmd_add_attribute(self, args=""):
        """Add attribute to users that don't already have it"""
        if not self.selected_users:
            print("❌ No users selected")
            return

        if not args:
            print("❓ Usage: add_attr [attribute] [default_value]")
            print("   Examples:")
            print("   add_attr gold 0")
            return

        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            print("❌ Missing default value")
            print("   Usage: add_attr [attribute] [default_value]")
            return

        key, default_str = parts
        default_value = convert_value(default_str)

        # Add attribute to selected users that don't have it
        updated = 0
        for user_id in self.selected_users:
            if key not in self.service.get_user(user_id):
                self.service.set(user_id, key, default_value)
                updated += 1

        print(f"✅ Added '{key}' with default value {repr(default_value)} to {updated} users")

    def cmd_set_attribute(self, args=""):
        """Set attribute for selected users"""
        if not self.selected_users:
            print("❌ No users selected")
            return

        if not args:
            print("❓ Usage: set_attr [attribute] [value]")
            print("   Examples:")
            print("   set_attr gems 100")
            return

        parts = args.split(maxsplit=1)

        # first argument must be a string
        part_0_type = type(convert_value(parts[0]))
        if part_0_type is not str:
            print(f"❌ Invalid tag type: {part_0_type}")
            return

        if len(parts) < 2:
            print("❌ Missing value")
            print("   Usage: set_attr [attribute] [value]")
            return

        key, value_str = parts
        value = convert_value(value_str)

        # Set attribute for selected users
        updated = 0
        for user_id in self.selected_users:
            self.service.set(user_id, key, value)
            updated += 1

        print(f"✅ Set '{key}' = {repr(value)} for {updated} users")

    def find_users_by_feature(self, args="") -> list:
        """Returns the list of users where a feature has a specific value"""
        parts = args.strip().split(maxsplit=1)
        feature, value_str = parts
        target_value = convert_value(value_str)

        # Get all user IDs
        user_ids = self.service.get_user_ids()
        if not user_ids:
            print("❌ No users found")
            return []

        # Find users matching the criteria
        matched_users = []
        for user_id in user_ids:
            user_data = self.service.get_user(user_id)
            if feature in user_data:
                current_value = user_data[feature]
                if current_value == target_value:
                    matched_users.append(user_id)
            elif target_value is None:
                # Field doesn't exist, which matches "None" search
                matched_users.append(user_id)

        if not matched_users:
            print(f"❌ No users found where {feature} = {repr(target_value)}")
            return []

        # Add matched users to selection (avoid duplicates)
        new_selection_count = 0
        for user_id in matched_users:
            if user_id not in self.selected_users:
                self.selected_users.append(user_id)
                new_selection_count += 1

        return matched_users

    def cmd_get_attribute(self, args=""):
        """Get an attribute's value for selected users"""
        if not self.selected_users:
            print("❌ No users selected")
            return

        if not args:
            print("❓ Usage: show [attribute]")
            print("   Examples:")
            print("   show gems")
            return

        keys = args.strip().split(maxsplit=1)

        if len(keys) == 1:
            # list values of that key for selected users
            print(f"\n🔍 Getting attribute '{keys[0]}' for {len(self.selected_users)} selected users:")
            for uid in self.selected_users:
                i = self.get_user_index(uid)
                value = self.service.get(uid, keys[0])
                emoji = self.service.get(uid, 'emoji')
                username = self.service.get(uid, 'username')
                print(f"{i:3} {uid:12} {repr(value):16} {emoji} {username}")
        elif len(keys) == 2:
            # list all users that have a certain value for that feature
            ...

    def cmd_remove_attribute(self, args=""):
        """Remove attribute from selected users"""
        if not self.selected_users:
            print("❌ No users selected")
            return

        if not args:
            print("❓ Usage: remove_attr [attribute]")
            print("   Examples:")
            print("   remove_attr gold")
            return

        key = args.strip()

        # Remove attribute from selected users
        removed = 0
        for user_id in self.selected_users:
            if key in self.service.get_user(user_id):
                self.service.delete_attribute(user_id, key)
                removed += 1

        print(f"✅ Removed '{key}' from {removed} users")

    def cmd_add_user(self, args=""):
        """Add a new user"""
        user_id = None
        username = input("Enter username: ").strip()
        if not username:
            print("❌ Username cannot be empty")
            return

        # Get user ID
        while True:
            id_input = input("Enter Telegram user ID: ").strip()
            if not id_input:
                print("❌ User ID cannot be empty")
                continue

            try:
                user_id = int(id_input)
                if user_id <= 0:
                    print("❌ User ID must be positive")
                    continue

                # Check if ID already exists
                if user_id in self.service.get_user_ids():
                    print(f"❌ User ID {user_id} already exists!")
                    overwrite = input("Overwrite existing user? (y/n): ").strip().lower()
                    if overwrite != 'y':
                        continue
                    else:
                        break
                else:
                    break
            except ValueError:
                print("❌ User ID must be a valid integer")

        # Add or update the user
        self.service.add_user(user_id, username)
        print(f"✅ Added/updated user {user_id}: {username}")

    def cmd_remove_user(self, args=""):
        """Remove a user"""
        user_ids = self.service.get_user_ids()
        if not user_ids:
            print("❌ No users found")
            return

        print(f"\n👥 {len(user_ids)} users:")
        for i, uid in enumerate(user_ids):
            i = self.get_user_index(uid)
            emoji = self.service.get(uid, 'emoji')
            username = self.service.get(uid, 'username')
            print(f"{i:3}) {uid:11} {emoji} {username}")

        # Get user to remove
        selection = input("\nEnter user index to remove: ").strip()
        if not selection:
            return

        # Parse selection
        to_remove = self.parse_selection(selection)
        if not to_remove:
            return

        # Confirm removal
        print(f"\n⚠️ WARNING: About to remove {len(to_remove)} user(s)")
        for user_id in to_remove:
            print(f"  - {user_id} {self.service.get(user_id, 'username')}")

        confirm = input("\nConfirm removal? (y/n): ").strip().lower()
        if confirm != 'y':
            print("❌ Operation cancelled")
            return

        # Remove users
        removed = 0
        for user_id in to_remove:
            self.service.delete_user(user_id)
            if user_id in self.selected_users:
                self.selected_users.remove(user_id)
            removed += 1

        print(f"✅ Removed {removed} user(s)")

    @classmethod
    def cmd_quit(cls, args=""):
        """Exit the program gracefully"""
        print("👋 Goodbye!")
        return False  # Signal to stop the main loop


def main():
    editor = UserEditor()
    editor.run()


if __name__ == '__main__':
    main()
