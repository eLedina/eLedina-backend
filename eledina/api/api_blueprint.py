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
from core.models import Users, Blogs, Learning
from core.cachemanager import CacheGenerator
from core.types_ import JsonStatus


__version__ = "0.1.0"


api = Blueprint("api", __name__,
                static_folder="../../static/", template_folder="../../templates/",
                url_prefix="/api")


users = Users()
blogs = Blogs()
learning = Learning()
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

    Fields:
        primary: str - can be either email or username
        password: str

    Statuses:
        INVALID_ARGUMENT: one/more of the passed fields is incorrect
        WRONG_LOGIN_INFO: any of the login arguments are incorrect
        OK: everything went ok, new token generated

    :return: JSON(status, [token, ])
    """
    body = loads(request.data)

    try:
        primary = body["primary"]
        password = body["password"]
    except KeyError:
        abort(400, dict(description="Missing fields!"))
        return

    try:
        new_token = users.login_user(primary, password)
    except ForbiddenArgument:
        payload = {
            "status": JsonStatus.INVALID_ARGUMENT
        }
        return jsonify_response(payload, 403)

    except LoginFailed:
        payload = {
            "status": JsonStatus.WRONG_LOGIN_INFO
        }
        return jsonify_response(payload, 403)

    else:
        payload = {
            "status": JsonStatus.OK,
            "token": new_token
        }
        return jsonify_response(payload)


@api.route("/user", methods=["GET", "PATCH"])
@require_token
@token_rate_limit
def user_manage(user_id: int):
    """
    /user: Get or update user data

    Fields (any of):
        username: str
        fullname: str
        email: str

        password: str - "passwordCurrent" must be included
        passwordCurrent: str

    Statuses:
        WRONG_LOGIN_INFO: passwordCurrent was invalid
        INVALID_ARGUMENT: an invalid argument was passed or the id was invalid
        USER_ALREADY_EXISTS: username or email is already registered
        OK: everything ok, user fields updated

    :return: JSON(status)
    """
    data = loads(request.data)

    # TODO high rate-limiting for username and other changes
    if request.method == "PATCH":
        # Parse fields
        fields = {}

        username = data.get("username")
        fullname = data.get("fullname")
        email = data.get("email")
        password = data.get("password")
        password_current = data.get("passwordCurrent")

        # Add fields to "fields"
        if username:
            fields["username"] = username
        if fullname:
            fields["fullname"] = fullname

        if email:
            fields["email"] = email

        if password:
            # passwordCurrent MUST be present when changing password
            if not password_current:
                payload = {
                    "status": JsonStatus.INVALID_ARGUMENT
                }
                return jsonify_response(payload, 403)

            # If passwordCurrent is not correct, return 403
            if users._verify_password(password_current, user_id) is False:
                payload = {
                    "status": JsonStatus.WRONG_LOGIN_INFO
                }
                return jsonify_response(payload, 403)
            # Otherwise add to fields
            fields["password"] = password

        try:
            users.update_user(user_id, fields)
        except ForbiddenArgument:
            payload = {
                "status": JsonStatus.INVALID_ARGUMENT
            }
            return jsonify_response(payload, 400)
        except (UsernameAlreadyExists, EmailAlreadyRegistered):
            payload = {
                "status": JsonStatus.USER_ALREADY_EXISTS
            }
            return jsonify_response(payload, 403)
        else:
            payload = {
                "status": JsonStatus.OK
            }
            return jsonify_response(payload)


@api.route("/blog/new", methods=["POST"])
@ip_rate_limit
def blog_new():
    print(request.data)
    body = loads(request.data)

    title = body.get("title")
    content = body.get("content")
    date = body.get("date")
    author = body.get("author")

    # Class and function imported from models.py
    blogs.upload_blog(title, content, date, author)
    blogpack = {
        "status": JsonStatus.OK,
    }
    return jsonify_response(blogpack)
    # CacheGenerator().blog_cache()


@api.route("/blog/list", methods=["GET"])
@ip_rate_limit
def blog_get():
    # Class and function imported from models.py
    bpack = blogs.get_blog()

    return jsonify_response(bpack)


@api.route("/learning/new", methods=["POST"])
@ip_rate_limit
def learning_new():
    body = loads(request.data)

    title = body.get("title")
    content = body.get("content")
    date = body.get("date")
    subject = body.get("subject")
    author = body.get("author")

    learning.uploadQuestion(title, content, date, subject, author)
    blogpack = {
        "status": JsonStatus.OK,
    }
    return jsonify_response(blogpack)


@api.route("/learning/list", methods=["GET"])
@ip_rate_limit
def learning_get():
    qpack = learning.getQuestions()
    return jsonify_response(qpack)


@api.route("/learning/question", methods=["POST"])
@ip_rate_limit
def learning_question():
    id = loads(request.data)

    qpack = learning.getQuestion(id)
    return jsonify_response(qpack)
