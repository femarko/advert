from typing import Any
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity

from app import adv


jwt = JWTManager(app=adv)


def get_access_token(identity) -> str:
    return create_access_token(identity=identity)


def get_authorized_user_identity() -> Any:
    return get_jwt_identity()
