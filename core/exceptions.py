# coding=utf-8


class BackendException(Exception):
    """
    Base for all other exceptions.
    """
    pass


class ForbiddenArgument(BackendException):
    """
    Raised when an argument is invalid -> too long, invalid email, ...
    """
    pass


class LoginFailed(BackendException):
    """
    Raised when wrong login info is provided
    """
    pass


class UsernameAlreadyExists(BackendException):
    """
    Raised while registering when a username already exists
    """
    pass


class EmailAlreadyRegistered(BackendException):
    """
    Raised while registering when an email is already reigstered
    """