# coding=utf-8
import redis
from passlib.hash import pbkdf2_sha512

from .config import redis_config, SALT, ROUNDS
from .util import is_email, gen_id, gen_token
from .exceptions import ForbiddenArgument, LoginFailed
from .input_limits import UserLimits
from .types_ import Role


def get_redis_config(section):
    host = redis_config.get(section, "host", fallback="localhost")
    port = redis_config.get(section, "port", fallback=6379)
    password = redis_config.get(section, "password", fallback=None)
    db = redis_config.get(section, "db", fallback=0)

    return host, port, password, db


# CONNECT
"""

Database layout:
    Split into two parts, RedisData with pure and unlinked data and
                          RedisCache containing 'links' between data that can be generated on startup


"""
# RedisData
d_host, d_port, d_pass, d_db = get_redis_config("RedisData")
rd = redis.Redis(host=d_host, port=d_port,
                 password=d_pass, db=d_db)

# RedisCache
c_host, c_port, c_pass, c_db = get_redis_config("RedisCache")
rc = redis.Redis(host=c_host, port=c_port,
                 password=c_pass, db=c_db)


class Users:
    """
    Users are available in:

        RedisData under user:<id> (Hash)
            username: str
            fullname: str
            about: str
            email: str
            password: str
            role: int

        TODO \/
        RedisCache provides links:
            user_by_name (Hash)
                <username>:<user_id>
            user_by_email (Hash)
                <email>:<user_id>


    Tokens are available in:

        RedisData under multiple keys:
            auth:by_token (Hash)
                <token>: <userid>
            auth:by_user (Hash)
                <userid>: <token: str>

    """
    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Hashes the password with sha512 and a custom salt
        """
        # return pbkdf2_sha512.encrypt(password, rounds=ROUNDS, salt=SALT)
        return pbkdf2_sha512.using(rounds=ROUNDS, salt=SALT).hash(password)

    def _verify_password(self, password: str, user_id: int) -> bool:
        """
        Verifies that the password is correct
        """
        hashed = self._get_hashed_password(user_id)
        return pbkdf2_sha512.verify(password, hashed)

    def _change_token(self, user_id: int, new_token: str):
        # raise NotImplementedError
        current_token = rd.hget("auth:by_user", user_id)

        pipe = rd.pipeline()
        # Old token needs to be deleted first
        pipe.hdel("auth:by_token", current_token)
        pipe.hset("auth:by_token", new_token, user_id)
        # Can be overwritten
        pipe.hset("auth:by_user", user_id, new_token)

        pipe.execute()

    # USER CREATION
    def register_user(self, username: str, fullname: str, email: str, password: str):
        """
        Registers a new user

        username: str(
        """
        # Checks
        if not is_email(email) or len(email) > UserLimits.EMAIL_MAX_LENGTH:
            raise ForbiddenArgument("invalid email")
        if len(username) > UserLimits.USERNAME_MAX_LENGTH:
            raise ForbiddenArgument("username too long")
        if len(fullname) > UserLimits.FULLNAME_MAX_LENGTH:
            raise ForbiddenArgument("name too long")
        if len(password) > UserLimits.PASSWORD_MAX_LENGTH:
            raise ForbiddenArgument("password too long")

        payload = {
            "name": username,
            "fullname": fullname,
            "email": email,
            "password": self._hash_password(password)
            # role defaults to USER (0)
            # about defaults to empty
        }
        user_id = gen_id()

        rd.hmset(f"user:{user_id}", payload)

    # METHODS THAT OPERATE WITH TOKENS
    def login_user(self, email: str, password: str) -> str:
        """
        Logs in the user with the provided email and password.

        :return: Token to be used on sequential requests
        """
        # Get userid from email
        if len(email) > UserLimits.EMAIL_MAX_LENGTH:
            raise ForbiddenArgument("invalid email")

        user_id = rc.hget("user_by_email", email)

        # Verify password
        if not self._verify_password(password, user_id):
            raise LoginFailed("wrong password/email")

        new_token = gen_token()
        self._change_token(user_id, new_token)

        return new_token

    @staticmethod
    def verify_token(token: str):
        """
        Returns a userid from the provided token - used on requests with restricted access to verify user
        :return: user id
        """
        return rd.hget("auth:by_token", token)

    # THESE FUNCTIONS NEED ID'S
    def get_username(self, user_id):
        raise NotImplementedError

    def get_full_name(self, user_id):
        raise NotImplementedError

    def get_description(self, user_id):
        raise NotImplementedError

    def get_email(self, user_id):
        raise NotImplementedError

    def _get_hashed_password(self, user_id):
        raise NotImplementedError