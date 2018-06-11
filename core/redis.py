# coding=utf-8
import redis
import logging

from .config import redis_config
from .util import Singleton


def get_redis_config(section):
    host = redis_config.get(section, "host", fallback="localhost")
    port = redis_config.get(section, "port", fallback=6379)
    password = redis_config.get(section, "password", fallback=None)
    db = redis_config.get(section, "db", fallback=0)

    return host, port, password, db


log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

# CONNECT
"""

Database layout:
    Split into two parts, RedisData with pure and unlinked data and
                          RedisCache containing 'links' between data that can be generated on startup


"""


class RedisData(redis.Redis, metaclass=Singleton):
    def __init__(self):
        log.info("Creating instance of RedisData")
        d_host, d_port, d_pass, d_db = get_redis_config("RedisData")

        super().__init__(host=d_host, port=d_port,
                         password=d_pass, db=d_db,
                         socket_connect_timeout=15)

        try:
            self.echo("Echo dis")
        except redis.ConnectionError:
            log.critical("RedisData connection could not be established, exiting!")
            exit(4)
        else:
            log.info("RedisData connection successful")


class RedisCache(redis.Redis, metaclass=Singleton):
    def __init__(self):
        log.info("Creating instance of RedisCache")
        d_host, d_port, d_pass, d_db = get_redis_config("RedisCache")

        super().__init__(host=d_host, port=d_port,
                         password=d_pass, db=d_db,
                         socket_connect_timeout=15)

        try:
            self.echo("Echo dis")
        except redis.ConnectionError:
            log.critical("RedisCache connection could not be established, exiting!")
            exit(4)
        else:
            log.info("RedisCache connection successful")


# Make first instance to check connection
RedisData()
RedisCache()
