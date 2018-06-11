# coding=utf-8
import logging

from .util import Singleton, decode
from .redis import rd, rc


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
        pass

    @staticmethod
    def _wipe_cache():
        """
        Wipes the whole RedisCache database.
        """
        log.warning("Wiping cache!")
        rc.flushdb()
        log.warning("Cache wiped!")

    def generate_cache(self):
        self._wipe_cache()

        # USER cache
        # user:by_username and user:by_email
        count = 0
        log.info("Generating user cache...")

        for key in rd.scan_iter(match="user:*"):
            key = bytes(key).decode(encoding="utf-8")
            user_id = key.split(":", maxsplit=1)[1]
            log.info(f"Processing {user_id}")
            count += 1

            user = decode(rd.hgetall(key))

            username = user.get("name")
            email = user.get("email")

            rc.hset("user:by_username", username, user_id)
            rc.hset("user:by_email", email, user_id)

        log.info(f"Generated user cache with {count} entries.")


        # TODO


