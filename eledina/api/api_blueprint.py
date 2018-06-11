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
from core.exceptions import UserAlreadyExists
from core.models import Users
from core.cachemanager import CacheGenerator


__version__ = "0.1.0"


api = Blueprint("api", __name__,
                static_folder="../../static/", template_folder="../../templates/",
                url_prefix="/api")


users = Users()
CacheGenerator().generate_cache()


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


# ERROR HANDLERS
@api.errorhandler(400)
def bad_request(error):
    payload = {
        "message": str(error.description) or "Bad request.",
    }

    return jsonify_response(payload, 400)


@api.errorhandler(403)
def forbidden(error):
    payload = {
        "message": str(error.description) or "Missing permissions.",
    }

    return jsonify_response(payload, 403)


@api.errorhandler(404)
def not_found(_):
    payload = {
        "message": "Invalid endpoint!",
    }

    return jsonify_response(payload, 404)


@api.errorhandler(409)
def conflict(error):
    payload = {
        "message": str(error.description) or "Unknown conflict.",
    }

    return jsonify_response(payload, 409)


@api.errorhandler(429)
def rate_limit(error):
    payload = {
        "message": str(error.get("message")) or "Too many requests.",
        "try_in": float(error.get("try_in"))
    }

    return jsonify_response(payload, 429)


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


@api.route("/register", methods=["POST"])
@ip_rate_limit
def register():
    """
    Registers a user

    Fields: username, name, surname, email, password
    :return:
    """
    body = loads(request.data)

    # TODO
    try:
        username = body["username"]
        name = body["name"]
        surname = body["surname"]
        email = body["email"]
        password = body["password"]

        fullname = f"{name}{surname}"
    except KeyError:
        abort(400, dict(description="Invalid fields!"))
        return

    # Additionally verifies data
    try:
        token = users.register_user(username, fullname, email, password)
    except UserAlreadyExists:
        payload = {
            "status": "USER_ALREADY_EXISTS",
        }
    else:
        payload = {
            "status": "OK",
            "token": token,
        }

    return jsonify_response(payload)


@api.route("/login", methods=["POST"])
@ip_rate_limit
def login():
    body = loads(request.data)

    # TODO


