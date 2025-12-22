# scripts/check_users.py
import json
from omar_bot.config.settings import USERS_DIR


def main():
    if not USERS_DIR.exists():
        print(f"❌ Directory not found: {USERS_DIR}")
        return

    json_files = list(USERS_DIR.glob("*.json"))
    if not json_files:
        print(f"❌ No JSON user files found in {USERS_DIR}")
        return

    print(f"\n🔍 Found {len(json_files)} user(s). Loading...\n")

    for json_file in sorted(json_files, key=lambda f: int(f.stem)):
        try:
            user_id = json_file.stem
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(f"User ID: {user_id}")
            for key, value in data.items():
                print(f" {key}: {value}")
            print()

        except Exception as e:
            print(f"❌ Failed to read {json_file.name}: {e}")

    print(f"✅ Checked {len(json_files)} users.")


if __name__ == "__main__":
    main()
