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


def gen_id(byte_size=25):
    """
    Generate a 'unique' id:
        secondsSinceYear+randomBits
    """
    today = datetime.datetime.now()
    year = datetime.datetime(year=today.year, month=1, day=1)

    td = int((today - year).total_seconds())
    gen = str(uuid.uuid4().int)[:byte_size]
    return int(str(td) + gen)


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
