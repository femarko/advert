from typing import Any

from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity

from app import adv
from app.error_handlers import HttpError
from app.models import UserColumns, AdvertisementColumns

jwt = JWTManager(app=adv)


def get_access_token(identity: UserColumns) -> str:
    """
    Create access token for user authentication, utilizing ``flask_jwt_extended.create_access_token()``.

    :param identity: a User model attribute
    :type identity: Any
    :return: access token
    :rtype: str
    """
    return create_access_token(identity=identity)


def get_authenticated_user_identity() -> Any:
    """
    Returns a result of ``flask_jwt_extended.get_jwt_identity()``.

    :return: value of an "identity" parameter, passed to ``flask_jwt_extended.create_access_token()``.
    :rtype: Any
    """
    return get_jwt_identity()


# def check_current_user(current_user_id: int, user_id: int) -> bool:
#     """
#     The function checks, whether an integer, passed as "user_id" parameter equals to the authenticated (current)
#     user's ID.
#
#     :param current_user_id: authenticated user's ID
#     :type current_user_id: int
#     :param user_id: an integer, which is a subject to check
#     :type user_id: int
#     :return: True | False
#     :rtype: bool
#     """
#     if user_id == current_user_id:
#         return True
#     return False


def check_current_user(user_id: int | None = None, get_cuid: bool = True) -> int | None:
    current_user_id: int = get_jwt_identity()
    if user_id is None or user_id == current_user_id:
        if get_cuid is True:
            return current_user_id
        else:
            return
    raise HttpError(status_code=403, description="Forbidden.")
