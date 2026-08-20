import secrets
import string

ALPHABET = string.ascii_letters + string.digits
LENGTH = 7


def generate_short_code() -> str:
    """Random base62 code."""
    return "".join(secrets.choice(ALPHABET) for _ in range(LENGTH))

