from typing import List
import hashlib
from omar_bot.config.settings import BOT_TOKEN, RANDOM_SALT, ADMIN_IDS


def convert_value(s: str):
    """
    Convert the input value to the appropriate type.
    :param s: string
    :return: value of the appropriate type
    """
    s = s.strip()

    if not s:
        return None
    if s.lower() == 'none':
        return None
    if s.lower() == 'true':
        return True
    if s.lower() == 'false':
        return False
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


def convert_string(s: str) -> List:
    """
    Convert 'str(list)' back to the original list
    :param s:
    :return:
    """
    for c in "[,]":
        s = s.replace(c, " ")
    print(s)
    parts = [part.strip() for part in s.split(" ")]
    parts = [convert_value(part) for part in parts if part]
    return parts


def sha256_hash(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def env_sanity_check():
    """Confirms that the env variables have been set"""
    variables = {
        "BOT_TOKEN": BOT_TOKEN,
        "RANDOM_SALT": RANDOM_SALT,
        "ADMIN_IDS": ADMIN_IDS,
    }
    for name, value in variables.items():
        if not value:
            raise ValueError(f'Set {name} in the ".env" ({value})')
