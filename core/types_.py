# coding=utf-8


class Role:
    USER = 0
    # NOT USED
    MODERATOR = 1
    ADMIN = 2


class JsonStatus:
    OK = "ok"

    INVALID_ARGUMENT = "invalid_argument"
    WRONG_LOGIN_INFO = "wrong_login_info"

    USER_ALREADY_EXISTS = "user_already_exists"
    EMAIL_ALREADY_REGISTERED = "email_registered"
