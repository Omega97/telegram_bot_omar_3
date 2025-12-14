import hashlib


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


def convert_string(s):
    """
    Convert str(list) back to the original list
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
