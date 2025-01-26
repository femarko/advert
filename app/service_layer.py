from datetime import datetime
from typing import Any, Callable, Protocol, Optional

from flask import request, Response
from sqlalchemy.exc import IntegrityError

import app.authentication
from app import models, adv, validation, pass_hashing, services
from app.error_handlers import HttpError
from app.errors import NotFoundError, ValidationError, AccessDeniedError, FailedToGetResultError, CurrentUserError, \
    AlreadyExistsError
from app.repository.filtering import get_list_or_paginated_data

import logging

from app.models import ModelClass, User, Advertisement
from app.repository.filtering import FilterTypes, UserColumns, AdvertisementColumns, Comparison
from app.base_resut import BaseResult

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


@adv.before_request
def before_request() -> None:
    session = models.session_maker()
    request.session = session


@adv.after_request
def after_request(response: Response) -> Response:
    request.session.close()
    return response


def process_result(result: BaseResult):
    if result.errors:
        raise FailedToGetResultError(f"{result.errors}")
    return result.result


def get_user_data(user_id: int, check_current_user_func: Callable, uow):
    current_user_id: int = check_current_user_func(user_id=user_id, get_cuid=True)
    with uow:
        user = uow.users.get(current_user_id)
    return services.get_params(model=user)


def create_user(user_data: dict[str, str], validate_func: Callable, hash_pass_func: Callable, uow):
    validated_data = validate_func(**user_data)
    validated_data["password"] = hash_pass_func(password=validated_data["password"])
    user = services.create_user(**validated_data)
    with uow:
        uow.users.add(user)
        uow.commit()
        user_id: int = user.id
        return user_id


def update_user(user_id: int, check_current_user_func: Callable, validate_func: Callable,
                hash_pass_func: Callable, new_data: dict[str, str], uow) -> dict:
    curent_user_id: int = check_current_user_func(user_id=user_id)
    validated_data: dict[str, str] = validate_func(**new_data)
    if validated_data.get("password"):
        validated_data["password"] = hash_pass_func(password=validated_data["password"])
    with uow:
        current_user: User = uow.users.get(instance_id=curent_user_id)
        updated_user = services.update_instance(instance=current_user, new_attrs=validated_data)
        uow.users.add(updated_user)
        uow.commit()
        updated_user_params = services.get_params(model=updated_user)
        return updated_user_params


def get_related_advs(authenticated_user_id: int,
                     check_current_user_func: Callable,
                     uow,
                     page: Optional[int] = None,
                     per_page: Optional[int] = None) -> dict[str, int | list[ModelClass]]:
    current_user_id = check_current_user_func(user_id=authenticated_user_id)
    with uow:
        paginated_data = uow.advs.get_list_or_paginated_data(filter_type=FilterTypes.COLUMN_VALUE,
                                                             comparison=Comparison.IS,
                                                             column=AdvertisementColumns.USER_ID,
                                                             column_value=current_user_id,
                                                             paginate=True,
                                                             page=page,
                                                             per_page=per_page)
        return paginated_data


def delete_user(user_id: int, check_current_user_func: Callable, uow) -> dict[str, str | int]:
    current_user_id: int = check_current_user_func(user_id=user_id)
    with uow:
        user_to_delete: User = uow.users.get(current_user_id)
        if not user_to_delete:
            raise app.errors.NotFoundError
        deleted_user_params: dict[str, str | int] = services.get_params(model=user_to_delete)
        uow.users.delete(user_to_delete)
        uow.commit()
    return deleted_user_params


def create_adv(get_auth_user_id_func: Callable, validate_func: Callable, adv_params: dict[str, str | int], uow) -> int:
    authenticated_user_id: int = get_auth_user_id_func()
    validated_data = validate_func(**adv_params)
    validated_data |= {"user_id": authenticated_user_id}
    adv = services.create_adv(**validated_data)
    with uow:
        uow.advs.add(adv)
        uow.commit()
        return adv.id


def update_adv(
        adv_id: int, new_params: dict, check_current_user_func: Callable, validate_func: Callable, uow
) -> dict[str, str | int]:
    with uow:
        adv: Advertisement = uow.advs.get(instance_id=adv_id)
        if not adv:
            raise app.errors.NotFoundError(message_prefix="The advertisement")
        check_current_user_func(user_id=adv.user_id)
        validated_data: dict[str, str] = validate_func(**new_params)
        updated_adv: Advertisement = services.update_instance(instance=adv, new_attrs=validated_data)
        uow.advs.add(updated_adv)
        uow.commit()
        updated_adv_params: dict = services.get_params(model=updated_adv)
        return updated_adv_params


def get_users_list(column: UserColumns, column_value: str | int | datetime, uow) -> list[User]:
    with uow:
        results = uow.users.get_list_or_paginated_data(filter_type=FilterTypes.COLUMN_VALUE,
                                                       comparison=Comparison.IS,
                                                       column=column,
                                                       column_value=column_value)
        # users_list: list[User] = process_result(result=results)
        # return users_list
        return results


def get_user_by_id(user_id: int, uow):
    with uow:
        user_instance = uow.users.get(user_id)
    return user_instance


def get_adv_params(adv_id: int, check_current_user_func: Callable, uow) -> dict[str, str | int]:
    with uow:
        adv: Advertisement = uow.advs.get(instance_id=adv_id)
    try:
        check_current_user_func(user_id=adv.user_id)
        return services.get_params(model=adv)
    except AttributeError:
        raise app.errors.NotFoundError(message_prefix="The advertisement")


def search_advs_by_text(
        column: UserColumns | AdvertisementColumns,
        column_value: str | int | datetime,
        uow,
        page: Optional[str] = None,
        per_page: Optional[str] = None
) -> dict[str, str | int]:
    with uow:
        paginated_res: dict[str, str | int] = uow.advs.get_list_or_paginated_data(
            filter_type=FilterTypes.SEARCH_TEXT, comparison=Comparison.IS, column=column, column_value=column_value,
            page=page, per_page=per_page, paginate=True
        )
    return paginated_res


def add_model_instance(model_instance: ModelClass) -> ModelClass:
    try:
        request.session.add(model_instance)
        request.session.commit()
    except IntegrityError:
        raise HttpError(409, "user already exists")
    return model_instance


def edit_model_instance(model_instance: ModelClass, new_data: dict) -> ModelClass:
    for key, value in new_data.items():
        setattr(model_instance, key, value)
    request.session.add(model_instance)
    request.session.commit()
    return model_instance


def delete_model_instance(model_instance: ModelClass):
    request.session.delete(model_instance)
    request.session.commit()


def validate(validation_func: Callable[..., BaseResult], input_data: dict[str, Any]) -> dict[str, Any]:
    validation_result = validation_func(validation_model=validation.Login, data=input_data)
    if validation_result.errors:
        raise ValidationError(f"{validation_result.errors}")
    return validation_result.result


def check_current_user(checking_func: Callable[[Optional[int]], BaseResult], user_id: Optional[int]) -> int:
    try:
        current_user_id = process_result(result=checking_func(user_id))
        return current_user_id
    except FailedToGetResultError:
        raise CurrentUserError


def jwt_auth(validate_func: Callable,
             check_pass_func: Callable[..., bool],
             grant_access_func: Callable,
             credentials: dict,
             uow) -> str:
    try:
        validated_data = validate_func(**credentials)
        user: User = \
            get_users_list(column=UserColumns.EMAIL, column_value=validated_data[UserColumns.EMAIL], uow=uow)[0]
        if check_pass_func(password=validated_data["password"], hashed_password=user.password):
            access_token: str = grant_access_func(identity=user.id)
            return access_token
        raise app.errors.AccessDeniedError
    except IndexError:
        raise app.errors.AccessDeniedError
