# coding=utf-8
import time
from passlib.hash import pbkdf2_sha512

from .util import is_email, gen_id, gen_token, Singleton, decode
from .exceptions import ForbiddenArgument, LoginFailed, UsernameAlreadyExists, EmailAlreadyRegistered
from .input_limits import UserLimits
from .config import SALT, ROUNDS
from .cachemanager import CacheGenerator
from .types_ import FieldUpdateType

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
        self.cache = CacheGenerator()

    @staticmethod
    def _hash_password(password: str) -> str:
        """
        Hashes the password with sha512 and a custom salt
        """
        # return pbkdf2_sha512.encrypt(password, rounds=ROUNDS, salt=SALT)
        return pbkdf2_sha512.using(rounds=ROUNDS, salt=SALT).hash(password)

    @staticmethod
    def _is_valid_userid(user_id: int):
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

    @staticmethod
    def _validate_user_fields(fields: dict):
        """
        Universal check for user fields

        :param fields: dict containing key-value pairs for user attributes
        :raise: ForbiddenArgument if invalid
        :return: bool
        """
        # Checks
        for k, v in fields.items():
            if k == "username":
                if len(v) > UserLimits.USERNAME_MAX_LENGTH or len(v) < UserLimits.USERNAME_MIN_LENGTH:
                    raise ForbiddenArgument("invalid username")

            elif k == "fullname":
                if len(v) > UserLimits.FULLNAME_MAX_LENGTH or len(v) < UserLimits.USERNAME_MIN_LENGTH:
                    raise ForbiddenArgument("invalid full name")

            elif k == "email":
                if not is_email(v) or len(v) > UserLimits.EMAIL_MAX_LENGTH or len(v) < UserLimits.EMAIL_MIN_LENGTH:
                    raise ForbiddenArgument("invalid email")

            elif k == "password":
                if len(v) > UserLimits.PASSWORD_MAX_LENGTH or len(v) < UserLimits.PASSWORD_MIN_LENGTH:
                    raise ForbiddenArgument("invalid password")

    # USER CREATION
    def register_user(self, username: str, fullname: str, email: str, password: str) -> str:
        """
        Registers a new user
        """
        payload = {
            "username": username,
            "fullname": fullname,
            "email": email,
            "password": password
        }
        # Verify fields
        self._validate_user_fields(payload)

        # Check if users already exist
        if self.rc.hexists("user:by_username", username):
            raise UsernameAlreadyExists
        if self.rc.hexists("user:by_email", email):
            raise EmailAlreadyRegistered

        payload.update({
            "password": self._hash_password(password),
            "reg_on": int(time.time())
            # role defaults to USER (0)
            # about defaults to empty
        })

        # Generate id and set info
        user_id = gen_id()
        self.rd.hmset(f"user:{user_id}", payload)

        # Generate and return token
        new_token = gen_token()
        self._change_token(user_id, new_token)

        # UPDATE CACHE for this user (so others can't register with the same username or email)
        self.cache.cache_single_user(user_id)

        return new_token

    # METHODS THAT OPERATE WITH TOKENS
    def login_user(self, primary: str, password: str) -> str:
        """
        Logs in the user with the provided email and password.

        :param: primary: Primary identification (email or username)
        :return: Token to be used on sequential requests
        """
        # Validate fields
        if len(primary) < UserLimits.EMAIL_MIN_LENGTH or len(primary) > UserLimits.EMAIL_MAX_LENGTH:
            raise ForbiddenArgument("invalid primary")

        self._validate_user_fields({"password": password})

        # Get user_id from email
        user_id = decode(self.rc.hget("user:by_email", primary))
        # User didn't pass email, but username
        if not user_id:
            user_id = decode(self.rc.hget("user:by_username", primary))

        # If user_id is still None that means incorrect credentials were sent
        if not user_id:
            raise LoginFailed("wrong password/email")

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
        return decode(self.rd.hget("auth:by_token", token))

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

    def _set_user_field(self, user_id: int, field: str, value: str, data):
        """
        Sets a users field to a value

        :param: user_id - ID of the user you want to modify
        :param: field - the field you want to update
        :param: value - what value to set the field to
        :param: data - user fields before update for caching
        """
        if field not in Users.USER_ATTR_WHITELIST:
            raise ForbiddenArgument("invalid field")

        # Do an assortment of checks
        if field == "username" and self.rc.hexists("user:by_username", value):
            raise UsernameAlreadyExists("username taken")
        if field == "email" and self.rc.hexists("user:by_email", value):
            raise EmailAlreadyRegistered("email already registered")
        if field == "password":
            raise ForbiddenArgument("can't update password via _set_user_field")
        if field == "reg_on":
            raise ForbiddenArgument("can't update reg_on via _set_user_field")

        response = decode(self.rd.hset(f"user:{user_id}", field, value))

        # Update cache if needed
        if field == "username":
            prev = data["username"]
            self.cache.cache_user_field_update(user_id, FieldUpdateType.USERNAME_UPDATE, prev, value)
        elif field == "email":
            prev = data["email"]
            self.cache.cache_user_field_update(user_id, FieldUpdateType.EMAIL_UPDATE, prev, value)

    def update_user(self, user_id: int, fields: dict):
        if not self._is_valid_userid(user_id):
            raise ForbiddenArgument("invalid user_id")

        self._validate_user_fields(fields)
        # _set_user_field needs user data before update for caching
        user_data = self.get_user_info(user_id)

        # Iterates though fields and sets them in db
        update = all([self._set_user_field(user_id, f, v, user_data) for f, v in fields.items()])
        return update

    ###################
    # GETTER FUNCTIONS
    # THESE NEED ID'S
    ###################
    def get_user_info(self, user_id: int) -> dict:
        data = decode(self.rd.hgetall(f"user:{user_id}"))
        # passing password is not good even if hashed, so we remove it
        try:
            del data["password"]
        except KeyError:
            pass

        return data

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


class Blogs(metaclass=Singleton):

    def __init__(self):
        self.rd = RedisData()
        self.rc = RedisCache()

    def upload_blog(self, title: str, content: str, date: str) -> str:
        # Package form as gotten from api_blueprint.py
        blogpack = {
            "title": title,
            "content": content,
            "date": date
        }

        # Generates blog ID
        blogid = gen_id()
        # Stores data inside Redis Data
        self.rd.hmset(f"blog:{blogid}", blogpack)

    def get_blog(self):
        bpack = {}

        # Searches for every key with blog:... and gets it's data
        for id in self.rd.scan_iter(match="blog:*"):
            blog = decode(self.rd.hgetall(id))
            title = blog.get("title")
            content = blog.get("content")
            date = blog.get("date")
            id = id.decode('utf-8')

            bpack[id] = {
                "title": title,
                "content": content,
                # Since intiger won't work, it's a string
                "date": str(date)
            }

        return bpack
