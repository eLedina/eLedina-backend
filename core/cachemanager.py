# coding=utf-8
import logging

from .util import Singleton, decode
from .redis import RedisData, RedisCache


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

    def generate_cache(self, wipe_first=True):
        if wipe_first:
            self._wipe_cache()

        # "Premature optimization is the root of all evil" - Donald Knuth

        # USER cache
        # user:by_username and user:by_email
        count = 0
        log.info("Generating user cache...")

        for key in self.rd.scan_iter(match="user:*"):
            key = bytes(key).decode(encoding="utf-8")
            user_id = key.split(":", maxsplit=1)[1]
            log.debug(f"Processing {user_id}")
            count += 1

            user = decode(self.rd.hgetall(key))

            username = user.get("name")
            email = user.get("email")

            self.rc.hset("user:by_username", username, user_id)
            self.rc.hset("user:by_email", email, user_id)

        log.info(f"Generated user cache with {count} entries.")

        # TODO

    def blog_cache(self, wipe_first=True):
        if wipe_first:
            self._wipe_cache()

        log.info("Generating blog cache...")

        for key in self.rd.scan_iter(match="blog:*"):
            key = bytes(key).decode(encoding="utf-8")
            blogid = key.split(":", maxsplit=1)[1]
            log.debug(f"Processing {blogid}")
            count += 1

            blog = decode(self.rd.hgetall(key))

            title = blog.get("title")
            date = blog.get("date")

            self.rc.hset("blog:by_date", date, blogid)
