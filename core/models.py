# coding=utf-8
import time
from passlib.hash import pbkdf2_sha512

from .util import is_email, gen_id, gen_token, Singleton, decode
from .exceptions import ForbiddenArgument, LoginFailed, UsernameAlreadyExists, EmailAlreadyRegistered
from .input_limits import UserLimits
from .config import SALT, ROUNDS


from .redis import RedisData, RedisCache


class Users(metaclass=Singleton):
    """
    Users are available in:

        RedisData under user:<id> (Hash)
            username: str
            fullname: str (name and surname split with '|')
            about: str
            email: str
            password: str
            role: int
            reg_on: int

        RedisCache provides links:
            user:by_username (Hash)
                <username>:<user_id>
            user:by_email (Hash)
                <email>:<user_id>


    Tokens are available in:

        RedisData under multiple keys:
            auth:by_token (Hash)
                <token>: <userid>
            auth:by_user (Hash)
                <userid>: <token: str>

    """
    USER_ATTR_WHITELIST = ("username", "fullname", "about", "email", "password", "role", "reg_on")

    def __init__(self):
        self.rd = RedisData()
        self.rc = RedisCache()

    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Hashes the password with sha512 and a custom salt
        """
        # return pbkdf2_sha512.encrypt(password, rounds=ROUNDS, salt=SALT)
        return pbkdf2_sha512.using(rounds=ROUNDS, salt=SALT).hash(password)

    @staticmethod
    def _is_valid_userid(user_id: int):
        # TODO verify that it works
        # !! HARDCODED ID LENGTH !!
        # see gen_id() for explanation
        return isinstance(user_id, int) and len(str(user_id)) == 20

    def _verify_password(self, password: str, user_id: int) -> bool:
        """
        Verifies that the password is correct
        """
        hashed = self._get_hashed_password(user_id)
        return pbkdf2_sha512.verify(password, hashed)

    def _change_token(self, user_id: int, new_token: str):
        if not self._is_valid_userid(user_id):
            raise ForbiddenArgument("invalid user_id")

        # TODO token expiration
        current_token = self.rd.hget("auth:by_user", user_id)

        pipe = self.rd.pipeline()
        # Old token needs to be deleted first
        pipe.hdel("auth:by_token", current_token)
        pipe.hset("auth:by_token", new_token, user_id)
        # Can be overwritten
        pipe.hset("auth:by_user", user_id, new_token)

        pipe.execute()

    def _user_exists(self, username: str) -> bool:
        return self.rc.hexists("user:by_username", username)

    # USER CREATION
    def register_user(self, username: str, fullname: str, email: str, password: str) -> str:
        """
        Registers a new user
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

        # TODO check if username already exists
        # TODO check if email already exists
        if self.rc.hexists("user:by_username", username):
            raise UsernameAlreadyExists

        if self.rc.hexists("user:by_email", email):
            raise EmailAlreadyRegistered

        payload = {
            "name": username,
            "fullname": fullname,
            "email": email,
            "password": self._hash_password(password),
            "reg_on": int(time.time())
            # role defaults to USER (0)
            # about defaults to empty
        }
        # Generate id and set info
        user_id = gen_id()
        self.rd.hmset(f"user:{user_id}", payload)

        # Generate and return token
        new_token = gen_token()
        self._change_token(user_id, new_token)

        return new_token

    # METHODS THAT OPERATE WITH TOKENS
    def login_user(self, email: str, password: str) -> str:
        """
        Logs in the user with the provided email and password.

        :return: Token to be used on sequential requests
        """
        # Get userid from email
        if len(email) > UserLimits.EMAIL_MAX_LENGTH or not is_email(email):
            raise ForbiddenArgument("invalid email")
        if len(password) > UserLimits.PASSWORD_MAX_LENGTH:
            raise ForbiddenArgument("password too long")

        # TODO verify it works
        user_id = decode(self.rc.hget("user_by_email", email))

        if not user_id:
            raise LoginFailed("wrong password/email")
        # Verify password
        if not self._verify_password(password, user_id):
            raise LoginFailed("wrong password/email")

        new_token = gen_token()
        self._change_token(user_id, new_token)

        return new_token

    def verify_token(self, token: str) -> str:
        """
        Returns a userid from the provided token - used on requests with restricted access to verify user
        :return: user id
        """
        return self.rd.hget("auth:by_token", token)

    def _get_user_attr(self, user_id: int, attr: str) -> str:
        """
        Returns a value from user:* hash

        :param user_id: ID of the user
        :param attr: attribute to access
        :type attr: str

        :return: requested attribute value
        """
        if not self._is_valid_userid(user_id):
            raise ForbiddenArgument("invalid user_id")

        # Verify attr
        if attr not in Users.USER_ATTR_WHITELIST:
            raise ForbiddenArgument("invalid attribute")

        return decode(self.rd.hget(f"user:{user_id}", attr))

    ###################
    # GETTER FUNCTIONS
    # THESE NEED ID'S
    ###################
    def get_username(self, user_id: int) -> str:
        return self._get_user_attr(user_id, "username")

    def get_full_name(self, user_id: int) -> str:
        return self._get_user_attr(user_id, "fullname")

    def get_about(self, user_id: int) -> str:
        return self._get_user_attr(user_id, "about")

    def get_email(self, user_id: int) -> str:
        return self._get_user_attr(user_id, "email")

    def _get_hashed_password(self, user_id: int) -> str:
        return self._get_user_attr(user_id, "password")
