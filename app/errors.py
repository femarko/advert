from typing import Optional


class NotFoundError(Exception):
    def __init__(self, message_prefix: Optional[str] = ""):
        self.base_message = " is not found."
        self.message = message_prefix + self.base_message


class ValidationError(Exception):
    pass


class AccessDeniedError(Exception):
    def __init__(self, message: Optional[str] = "Invalid credentials."):
        self.message = message


class FailedToGetResultError(Exception):
    pass


class CurrentUserError(Exception):
    def __init__(self, message: Optional[str] = "Unavailable operation."):
        self.message = message


class AlreadyExistsError(Exception):
    def __init__(self, message_prefix: Optional[str] = ""):
        self.base_message = "with the provided params already existsts."
        self.message = message_prefix + self.base_message
