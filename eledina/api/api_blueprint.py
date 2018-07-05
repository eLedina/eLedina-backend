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
from core.exceptions import UsernameAlreadyExists, ForbiddenArgument, LoginFailed, EmailAlreadyRegistered
from core.models import Users
from core.models import Blogs
from core.cachemanager import CacheGenerator
from core.types_ import JsonStatus
import sys


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
        user_id = users.verify_token(token)
        if not token or not user_id:
            abort(403, "Invalid token")

        # See this \/
        return fn(int(user_id), *args, **kwargs)
    return inner


#################
# ERROR HANDLERS
# These error handlers catch abort() calls and return json alongside a http status
#################

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


#############
# API ROUTES
# Routes that are important for API calls
#############

@api.route("/version")
@ip_rate_limit
def version():
    """
    /version: version of the api

    Fields: none
    Statuses: none

    :return: JSON(version)
    """
    payload = {
        "version": __version__
    }

    return jsonify_response(payload)


@api.route("/ping")
@require_token
@token_rate_limit
def ping(_user_id: int):
    """
    /ping: connection test

    Fields: none
    Statuses: none

    :return: JSON(echo: str)
    """
    payload = {
        "echo": randint(1, 150)
    }

    return jsonify_response(payload)


@api.route("/register", methods=["POST"])
@ip_rate_limit
def register():
    """
    /register: Register a user and generate an access token

    Fields:
        username: str
        name: str
        surname: str
        email: str
        password: str

    Statuses:
        USER_ALREADY_EXISTS: username is taken
        OK: everything ok, user registered

    :return: JSON(status, [token, ])
    """
    body = loads(request.data)

    try:
        username = body["username"]
        name = body["name"]
        surname = body["surname"]
        email = body["email"]
        password = body["password"]

        fullname = f"{name}|{surname}"
    except KeyError:
        abort(400, dict(description="Invalid fields!"))
        return

    # Additionally verifies data
    try:
        token = users.register_user(username, fullname, email, password)
    except UsernameAlreadyExists:
        payload = {
            "status": JsonStatus.USER_ALREADY_EXISTS,
        }

        return jsonify_response(payload, 403)

    except EmailAlreadyRegistered:
        payload = {
            "status": JsonStatus.EMAIL_ALREADY_REGISTERED
        }

        return jsonify_response(payload, 403)

    else:
        payload = {
            "status": JsonStatus.OK,
            "token": token,
        }

        return jsonify_response(payload)


@api.route("/login", methods=["POST"])
@ip_rate_limit
def login():
    """
    /login: Login the user and generate an access token

    # TODO allow username login
    Fields:
        email: str
        password: str

    Statuses:
        INVALID_ARGUMENT: one/more of the passed fields is incorrect
        WRONG_LOGIN_INFO: any of the login arguments are incorrect
        OK: everything went ok, new token generated

    :return: JSON(status, [token, ])
    """
    body = loads(request.data)

    # TODO
    try:
        email = body["email"]
        password = body["password"]
    except KeyError:
        abort(400, dict(description="Missing fields!"))
        return

    try:
        new_token = users.login_user(email, password)
    except ForbiddenArgument:
        payload = {
            "status": JsonStatus.INVALID_ARGUMENT
        }
    except LoginFailed:
        payload = {
            "status": JsonStatus.WRONG_LOGIN_INFO
        }
    else:
        payload = {
            "status": JsonStatus.OK,
            "token": new_token
        }

    return jsonify_response(payload)


@api.route("/blog_writingpage", methods=["POST"])
def blog_writingpage():

    payload = request.get_json(silent=True)
    title = payload.get("title")
    content = payload.get("content")
    date = payload.get("date")
