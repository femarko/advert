class NotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class AccessDeniedError(Exception):
    pass


class FailedToGetResultError(Exception):
    pass


class CurrentUserError(Exception):
    pass


class AlreadyExistsError(Exception):
    pass
