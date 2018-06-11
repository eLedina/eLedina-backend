# coding=utf-8
import time
from passlib.hash import pbkdf2_sha512

from .util import is_email, gen_id, gen_token, Singleton
from .exceptions import ForbiddenArgument, LoginFailed
from .input_limits import UserLimits
from .config import SALT, ROUNDS


from .redis import rd, rc


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

        TODO \/
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

    @staticmethod
    def _change_token(user_id: int, new_token: str):
        # TODO token expiration
        current_token = rd.hget("auth:by_user", user_id)

        pipe = rd.pipeline()
        # Old token needs to be deleted first
        pipe.hdel("auth:by_token", current_token)
        pipe.hset("auth:by_token", new_token, user_id)
        # Can be overwritten
        pipe.hset("auth:by_user", user_id, new_token)

        pipe.execute()

    @staticmethod
    def _user_exists(username: str):
        return rc.hexists("user:by_username", username)

    # USER CREATION
    def register_user(self, username: str, fullname: str, email: str, password: str):
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
        rd.hmset(f"user:{user_id}", payload)

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