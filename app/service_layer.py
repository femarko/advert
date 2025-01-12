from datetime import datetime
from typing import Any, Callable, Protocol, Optional

from flask import request, Response
from sqlalchemy.exc import IntegrityError

import app.authentication
from app import models, adv, validation, pass_hashing
from app.error_handlers import HttpError
from app.repository.filtering import FilterResult, get_list_or_paginated_data

import logging

from app.models import ModelClass, User, Advertisement
from app.repository.filtering import FilterTypes, UserColumns, AdvertisementColumns, Comparison
from app.base_resut import BaseResult
from app.validation import ValidationResult

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


class NotFoundError(Exception):
    pass


class ValidationError(Exception):
    pass


class AccessDeniedError(Exception):
    pass


class FailedToGetResultError(Exception):
    pass


class CurrentUserError:
    pass


class AlreadyExistsError(Exception):
    pass


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


def get_user_data(user_id: int, uow):
    try:
        current_user_id: int = check_current_user(checking_func=app.authentication.check_current_user, user_id=user_id)
    except CurrentUserError:
        raise AccessDeniedError
    with uow:
        user = uow.users.get(current_user_id)
    if not user:
        raise NotFoundError
    return user.get_user_data()


def create_user(user_data: dict[str, str], uow):
    try:
        validated_data = process_result(result=validation.validate_user_data(**user_data))
        validated_data["password"] = pass_hashing.hash_password(password=validated_data["password"])
        user_instance = User(**validated_data)
        with uow as u:
            created_user: User = uow.users.add(user_instance)
            uow.commit()
            created_user_data: int = created_user.get_user_data()["id"]
            return created_user_data
    except FailedToGetResultError as e:
        raise ValidationError(e)
    except AlreadyExistsError:
        raise AlreadyExistsError(f"A user with the provided credentials already existsts.")



def get_related_advs(current_user_id: int, page: int, per_page: int, uow) -> dict[str, int | list[ModelClass]]:
    # with uow:
    #     filter_result = uow.advs.get_paginated(filter_type=FilterTypes.COLUMN_VALUE,
    #                                            column=AdvertisementColumns.USER_ID,
    #                                            column_value=current_user_id,
    #                                            comparison=Comparison.IS,
    #                                            page=page,
    #                                            per_page=per_page)
    #     filter_result.result["items"] = [item.get_adv_params() for item in filter_result.result["items"]]
    # return filter_result.result
    with uow:
        filter_result: Protocol[BaseResult] = uow.advs.get_paginated(filter_type=FilterTypes.COLUMN_VALUE,
                                                                     column=AdvertisementColumns.USER_ID,
                                                                     column_value=current_user_id,
                                                                     comparison=Comparison.IS,
                                                                     page=page,
                                                                     per_page=per_page)
        try:
            processed_result = process_result(result=filter_result)
        except FailedToGetResultError:
            raise ValidationError(f"{processed_result}")
        return processed_result


def get_users_list(column: UserColumns, column_value: str | int | datetime, uow) -> list[User]:
    with uow:
        results = uow.users.get_list_or_paginated_data(filter_func=get_list_or_paginated_data,
                                                       filter_type=FilterTypes.COLUMN_VALUE,
                                                       comparison=Comparison.IS,
                                                       column=column,
                                                       column_value=column_value)
        users_list: list[User] = process_result(result=results)
        return users_list


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
        filter_result.result["items"] = [
            {item.title: item.description} for item in filter_result.result["items"]
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
    if validation_result.errors:
        raise ValidationError(f"{validation_result.errors}")
    return validation_result.result


def check_current_user(checking_func: Callable[[Optional[int]], BaseResult], user_id: Optional[int]) -> int:
    try:
        current_user_id = process_result(result=checking_func(user_id))
        return current_user_id
    except FailedToGetResultError:
        raise CurrentUserError


def jwt_auth(validate_func: Callable[..., BaseResult],
             check_pass_func: Callable[..., bool],
             grant_access_func: Callable,
             credentials: dict,
             uow) -> str:
    validation_result = validate_func(**credentials)
    if validation_result.errors:
        raise ValidationError(f"{validation_result.errors}")
    validated_data = validation_result.result
    try:
        user: User = \
            get_users_list(column=UserColumns.EMAIL, column_value=validated_data[UserColumns.EMAIL], uow=uow)[0]
        if check_pass_func(password=validated_data["password"], hashed_password=user.password):
            access_token: str = grant_access_func(identity=user.id)
            return access_token
        raise AccessDeniedError(f"Invalid credentials.")
    except IndexError:
        raise AccessDeniedError(f"Invalid credentials.")
