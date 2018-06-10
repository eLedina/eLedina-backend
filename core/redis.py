# coding=utf-8
import redis

from .config import redis_config


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


