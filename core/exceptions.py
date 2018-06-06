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
