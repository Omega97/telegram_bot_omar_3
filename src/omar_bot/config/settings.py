from pathlib import Path
import os
from dotenv import load_dotenv
import logging


# Project root (where pyproject.toml is)
CONFIG_PATH = Path(__file__).parent
OMAR_BOT_PATH = CONFIG_PATH.parent
SRC_PATH = OMAR_BOT_PATH.parent
PROJECT_ROOT = SRC_PATH.parent


# Data directories
DATA_DIR = PROJECT_ROOT / "data"
PRIVATE_DIR = DATA_DIR / "PRIVATE"
USERS_DIR = PRIVATE_DIR / "users"
CANVAS_DIR = PRIVATE_DIR / "canvases"
DEFAULT_EMOJI_PATH = DATA_DIR / "default_emoji.txt"


# Load environment variables from .env file
load_dotenv()


# Retrieve the bot token from environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")


# Ensure the BOT_TOKEN is set, raise an error otherwise.
if not BOT_TOKEN:
    raise ValueError("The BOT_TOKEN environment variable is not set. Please create a .env file and add it.")


# Debug mode
DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes", "on")
LOG_LEVEL = logging.DEBUG if DEBUG else logging.INFO


# --- Other Settings (Optional) ---
ADMIN_IDS = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x]
PLACE_COOLDOWN_MINUTES = int(os.getenv("PLACE_COOLDOWN_MINUTES", "3"))
