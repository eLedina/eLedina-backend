# coding=utf-8
from flask import Blueprint, request, abort
from functools import wraps
from random import randint
try:
    from ujson import loads
except ImportError:
    from json import loads

from ..flask_util import jsonify_response
from .bucket import ip_rate_limit, token_rate_limit
from core.redis import Users


__version__ = "0.1.0"


api = Blueprint("eLedinaAPI", __name__,
                static_folder="../../static/", template_folder="../../templates/",
                url_prefix="/api")


# AUTHENTICATION
def require_token(fn):
    """
    FYI: adds another argument to the function: the current token
    :raise: HTTP 403 if the token is not valid
    """
    @wraps(fn)
    def inner(*args, **kwargs):
        token = request.headers.get("Authorization")
        user_id = Users.verify_token(token)
        if not token or not user_id:
            abort(403, "Invalid token")

        # See this \/
        return fn(int(user_id), *args, **kwargs)
    return inner


@api.route("/version")
@ip_rate_limit
def version():
    payload = {
        "version": __version__
    }

    return jsonify_response(payload)


@api.route("/test")
@require_token
@token_rate_limit
def test(_user_id: int):
    """
    /test: an endpoint to test connection
    :param _user_id:
    :return:
    """
    payload = {
        "echo": randint(1, 150)
    }

    return jsonify_response(payload)


@api.route("/login")
@ip_rate_limit
def login():
    body = loads(request.data)

    # TODO


