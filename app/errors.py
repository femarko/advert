class NotFoundError(Exception):
    message = "is not found."


class ValidationError(Exception):
    pass


class AccessDeniedError(Exception):
    message = "Invalid credentials."


class FailedToGetResultError(Exception):
    pass


class CurrentUserError(Exception):
    message = "Unavailable operation."


class AlreadyExistsError(Exception):
    message = "with the provided params already existsts."
