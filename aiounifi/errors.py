"""Aiounifi errors."""


class AiounifiException(Exception):
    """Base error for aiounifi."""


class RequestError(AiounifiException):
    """Unable to fulfill request.
    Raised when host or API cannot be reached.
    """


class ResponseError(AiounifiException):
    """Invalid response."""


class Unauthorized(AiounifiException):
    """Username is not authorized."""


class LoginRequired(AiounifiException):
    """User is logged out."""


class NoPermission(AiounifiException):
    """Users permissions are read only."""


class TwoFaTokenRequired(AiounifiException):
    """2 factor authentication token required."""


ERRORS = {
    "api.err.LoginRequired": LoginRequired,
    "api.err.Invalid": Unauthorized,
    "api.err.NoPermission": NoPermission,
    "api.err.Ubic2faTokenRequired": TwoFaTokenRequired,
}


def raise_error(error):
    type = error
    cls = ERRORS.get(type, AiounifiException)
    raise cls("{}".format(type))
