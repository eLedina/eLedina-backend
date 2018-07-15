# coding=utf-8
import logging

from .util import Singleton, decode
from .redis import RedisData, RedisCache
from .types_ import FieldUpdateType


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class CacheGenerator(metaclass=Singleton):
    """
    This class is used for generating cache from RedisData.

    RedisCache layout:

        user:by_username (Hash)
            <username>:<user_id>
        user:by_email (Hash)
            <email>:<user_id>

        # TODO
    """
    def __init__(self):
        self.rd = RedisData()
        self.rc = RedisCache()

    def _wipe_cache(self):
        """
        Wipes the whole RedisCache database.
        """
        self.rc.flushdb()
        log.warning("RedisCache wiped!")

    ##############################
    # CACHE GENERATORS for individual users
    # This is to be used for generating small chunks of cache when the server is already running.
    # Example: when a user registers
    #
    # All of these functions should have a prefix: cache_single_<type>
    ##############################
    def cache_single_user(self, user_id: int):
        user = decode(self.rd.hgetall(f"user:{user_id}"))

        username = user["username"]
        email = user["email"]

        pipe = self.rc.pipeline()

        pipe.hset("user:by_username", username, user_id)
        pipe.hset("user:by_email", email, user_id)

        pipe.execute()

    def cache_user_field_update(self, user_id: int, update_type: FieldUpdateType, previous: str, new: str):
        """
        Caches only one field update. Deletes the old cached field and puts the new one in.

        This function is necessary for fields:
            username: str
            email: str
        """
        # This should be called when the 'username' field is updated
        pipe = self.rc.pipeline()

        pipe.hdel(update_type, previous)
        pipe.hset(update_type, new, user_id)

        pipe.execute()
        log.debug(f"Updated single user field: {update_type}")

    ##############################
    # CACHE GENERATORS
    ##############################
    def _gen_user_cache(self):
        # USER cache
        # user:by_username and user:by_email
        count = 0
        log.info("Generating user cache...")

        for key in self.rd.scan_iter(match="user:*"):
            key = bytes(key).decode(encoding="utf-8")
            user_id = int(key.split(":", maxsplit=1)[1])

            log.debug(f"Processing {user_id}")
            count += 1
            self.cache_single_user(user_id)

        log.info(f"Generated user cache with {count} entries.")

    def generate_cache(self, wipe_first=True):
        if wipe_first:
            self._wipe_cache()

        # "Premature optimization is the root of all evil" - Donald Knuth

        # USER CACHE
        self._gen_user_cache()

        # TODO other types of cache
