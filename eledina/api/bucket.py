# coding=utf-8
import time
from functools import wraps
from flask import request, abort


class Bucket:
    __slots__ = ("last_cooldown", "_size", "_cooldown", "current_bucket")

    def __init__(self, limit: int=7, per: int=8):
        self.last_cooldown = time.time()

        self._size = limit
        self._cooldown = per
        self.current_bucket = 0

    def action(self):
        current_time = time.time()

        # If bucket cooldown is reached, reset the bucket
        if current_time - self.last_cooldown > self._cooldown:
            self.last_cooldown = current_time
            self.current_bucket = 0
            return True

        if self.current_bucket >= self._size:
            return False
        else:
            self.current_bucket += 1
            return True


ip_buckets = {}
token_buckets = {}


def _send_429(bucket):
    """
    Uses Flasks abort() to return a HTTP "429 Too Many Requests"
    """
    # Calculates bucket expiration time
    ttl = (bucket.last_cooldown + bucket._cooldown) - time.time()
    # log.info("{} is getting rate-limited for {}s".format(token, ttl))

    info = {
        "message": "Too many requests, slow down",
        "try_in": ttl,
    }
    abort(429, info)


def ip_rate_limit(fn):
    @wraps(fn)
    def inner(*args, **kwargs):
        ip = request.remote_addr

        # Add a bucket if not present
        if not ip_buckets.get(ip):
            b = Bucket()
            b.action()
            ip_buckets[ip] = b
        # Otherwise, verify that the user has some requests left in this time period
        else:
            bucket = ip_buckets[ip]

            if not bucket.action():
                _send_429(bucket)

        return fn(*args, **kwargs)

    return inner


def token_rate_limit(fn):
    @wraps(fn)
    def inner(token, *args, **kwargs):
        # Add a bucket if not present
        if not token_buckets.get(token):
            b = Bucket()
            b.action()
            token_buckets[token] = b
        # Otherwise, verify that the user has some requests left in this time period
        else:
            bucket = token_buckets[token]

            if not bucket.action():
                _send_429(bucket)

        return fn(*args, **kwargs)

    return inner
