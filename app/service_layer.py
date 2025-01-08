from datetime import datetime
from typing import Any, Callable, Literal

from flask import request, Response
from sqlalchemy.exc import IntegrityError

from app import models, adv, validation
from app.error_handlers import HttpError
from app.repository.filtering import filter_and_return_list, filter_and_return_paginated_data, FilterResult, \
    InvalidFilterParams, Params

import logging

from app.models import ModelClass, User, Advertisement
from app.repository.filtering import FilterTypes, UserColumns, AdvertisementColumns, Comparison
from app.repository.repository import Repository
from app.unit_of_work import UnitOfWork
from app.validation import ValidationResult
from app.base_resut import BaseResult

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class NotFound(Exception):
    pass


class ValidationFailed(Exception):
    pass


class AccessDenied(Exception):
    pass


@adv.before_request
def before_request() -> None:
    session = models.session_maker()
    request.session = session


@adv.after_request
def after_request(response: Response) -> Response:
    request.session.close()
    return response


def get_related_advs(current_user_id: int, page: int, per_page: int, uow) -> dict[str, int | list[ModelClass]]:
    with uow:
        filter_result = uow.advs.get_paginated(filter_type=FilterTypes.COLUMN_VALUE,
                                               column=AdvertisementColumns.USER_ID,
                                               column_value=current_user_id,
                                               comparison=Comparison.IS,
                                               page=page,
                                               per_page=per_page)
        filter_result.filtered_data["items"] = [item.get_adv_params() for item in filter_result.filtered_data["items"]]
    return filter_result.filtered_data


def get_users_list(column: UserColumns, column_value: str | int | datetime, uow) -> list[User]:
    with uow as uow:
        results = uow.users.get_list(
            filter_type=FilterTypes.COLUMN_VALUE, comparison=Comparison.IS, column=column, column_value=column_value
        )
        if results.status == "Failed":
            raise ValidationFailed(f"{results.errors}")
        return results.filtered_data


def get_user_by_id(user_id: int, uow):
    with uow:
        user_instance = uow.users.get(user_id)
    return user_instance


def get_adv(column: AdvertisementColumns, column_value: str | int | datetime, session) -> FilterResult:
    results: FilterResult = filter_and_return_list(session=session,
                                                   model_class=Advertisement,
                                                   filter_type=FilterTypes.COLUMN_VALUE,
                                                   comparison=Comparison.IS,
                                                   column=column,
                                                   column_value=column_value)
    return results


def search_advs_by_text(column: AdvertisementColumns,
                        column_value: str | int | datetime,
                        page: int,
                        per_page: int,
                        session) -> dict[str, int | list[dict[str, str]]]:
    filter_result: FilterResult = filter_and_return_paginated_data(session=session,
                                                                   model_class=Advertisement,
                                                                   filter_type=FilterTypes.SEARCH_TEXT,
                                                                   column=column,
                                                                   column_value=column_value,
                                                                   page=page,
                                                                   per_page=per_page)
    if filter_result.status == "OK":
        filter_result.filtered_data["items"] = [
            {item.title: item.description} for item in filter_result.filtered_data["items"]
        ]
    return filter_result


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
    if validation_result.status == "Failed":
        raise ValidationFailed(f"{validation_result.errors}")
    return validation_result.result


def jwt_auth(validate_func: Callable[..., BaseResult],
             check_pass_func: Callable[..., bool],
             grant_access_func: Callable,
             credentials: dict,
             uow) -> str:
    validation_result = validate_func(**credentials)
    if validation_result.status == "Failed":
        raise ValidationFailed(f"{validation_result.errors}")
    validated_data = validation_result.result
    try:
        user: User = \
            get_users_list(column=UserColumns.EMAIL, column_value=validated_data[UserColumns.EMAIL], uow=uow)[0]
        if check_pass_func(password=validated_data["password"], hashed_password=user.password):
            access_token: str = grant_access_func(identity=user.id)
            return access_token
        raise AccessDenied(f"Invalid credentials.")
    except IndexError:
        raise AccessDenied(f"Invalid credentials.")
