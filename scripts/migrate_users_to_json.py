import json
from pathlib import Path


# Paths
USERS_CSV_DIR = Path(r"C:\Users\monfalcone\PycharmProjects\telegram_bot_omar2\DATA\PRIVATE\users")
USERS_JSON_DIR = Path(r"C:\Users\monfalcone\PycharmProjects\telegram_bot_omar_3\data\PRIVATE\users")


def read_user_csv_file(file_path: Path):
    """Convert the csv user file to a dictionary."""
    result = {}
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ',' not in line:
                continue
            key, value = line.split(",", 1)
            # Try to convert value to int, float, bool, or None
            if value == 'None':
                value = None
            elif value.lower() == 'true':
                value = True
            elif value.lower() == 'false':
                value = False
            else:
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except ValueError:
                    pass  # keep as string
            result[key] = value
    return result


def main():
    print(f"🔍 Looking for CSV user files in {USERS_CSV_DIR}")
    if not USERS_CSV_DIR.exists():
        print("❌ Directory not found!")
        return

    # ✅ CREATE THE OUTPUT DIRECTORY IF IT DOESN'T EXIST
    USERS_JSON_DIR.mkdir(parents=True, exist_ok=True)

    converted = 0
    skipped = 0

    for csv_file in USERS_CSV_DIR.glob("*.csv"):
        user_id = csv_file.stem
        json_file = USERS_JSON_DIR / f"{user_id}.json"

        if json_file.exists():
            print(f"🟡 Skip {user_id}: JSON already exists")
            skipped += 1
            continue

        try:
            print(f"📄 Reading {csv_file.name}...")
            user_data = read_user_csv_file(csv_file)

            print(f"💾 Writing {json_file.name}...")
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(user_data, f, ensure_ascii=False, indent=2)

            converted += 1
        except Exception as e:
            print(f"❌ Failed to process {csv_file}: {e}")

    print(f"\n✅ Done! Converted {converted}, skipped {skipped}")


if __name__ == "__main__":
    main()
