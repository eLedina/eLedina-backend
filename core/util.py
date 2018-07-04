# coding=utf-8
import uuid
import secrets
import re
import datetime


class Singleton(type):
    """
    Only allows one instantiation. On subsequent __init__ calls, returns the first instance
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


def gen_id(id_size=12) -> int:
    """
    Generate a 'unique' id:
        random_bits+seconds_since_year_zero_padded

    The actual ID size is id_size + 8 (by default this makes the ID 20 digits long)
    """
    today = datetime.datetime.now()
    year = datetime.datetime(year=today.year, month=1, day=1)

    # Pad to be fixed 8 chars (the biggest number is 31556926, which has 8 digits)
    td = str(int((today - year).total_seconds())).zfill(8)
    gen = str(uuid.uuid4().int)[:id_size]

    return int(gen + td)


def gen_token():
    """
    Generate an access token (64 bits)
    """
    return secrets.token_urlsafe(64)


EMAIL_EXP = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")


def is_email(email: str) -> bool:
    """
    Checks an email to see if it is a valid address
    """
    return EMAIL_EXP.match(email) is not None


# REDIS DECODE FUNCTIONS
def decode(c):
    if c is None:
        return None

    return boolify(decode_auto(c))


def boolify(s):
    if s == "True":
        return True
    if s == "False":
        return False
    if s == "None":
        return None

    return s


def decode_auto(some):
    """
    Converts/decodes all kinds of types (mostly bytes) into their expected types
    """
    if isinstance(some, bytes):
        return decode_auto(some.decode())

    if isinstance(some, str):
        # Auto-convert numbers to int
        if some.isnumeric():
            return int(some)

        return boolify(some)

    if isinstance(some, int):
        return some

    if isinstance(some, dict):
        return dict(map(decode_auto, some.items()))
    if isinstance(some, tuple):
        return tuple(map(decode_auto, some))
    if isinstance(some, list):
        return list(map(decode_auto, some))
    if isinstance(some, set):
        return set(map(decode_auto, some))

    # If it's some other type, return it as is
    return some