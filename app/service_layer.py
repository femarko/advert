from datetime import datetime

from flask import request, Response
from sqlalchemy.exc import IntegrityError

from app import models, adv, filtering
from app.error_handlers import HttpError

import logging

from app.models import ModelClass, User, Advertisement
from app.filtering import FilterTypes, UserColumns, AdvertisementColumns, Comparison

logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


@adv.before_request
def before_request() -> None:
    session = models.Session()
    request.session = session


@adv.after_request
def after_request(response: Response) -> Response:
    request.session.close()
    return response


def get_related_advs(current_user_id: int, page: int, per_page: int, session) -> dict[str, int | list[Advertisement]]:
    result: dict[str, int | list[Advertisement]] = filtering.filter_and_return_paginated_data(
        session=session,
        model_class=Advertisement,
        filter_type=FilterTypes.COLUMN_VALUE,
        column=AdvertisementColumns.USER_ID,
        column_value=current_user_id,
        page=page,
        per_page=per_page
    )
    return result


def get_user(column: UserColumns, column_value: str | int | datetime, session) -> User:
    results: list[User] = filtering.filter_and_return_list(session=session,
                                                           model_class=User,
                                                           filter_type=FilterTypes.COLUMN_VALUE,
                                                           comparison=Comparison.IS,
                                                           column=column,
                                                           column_value=column_value)
    if results:
        user_instance: User = results[0]
        return user_instance
    raise HttpError(status_code=404, description=f"Entry is not found.")


def get_adv(column: AdvertisementColumns, column_value: str | int | datetime, session) -> Advertisement:
    filter_object = filtering.Filter(session=session)
    results: list[Advertisement] = filter_object.get_list(model_class=Advertisement,
                                                          filter_type=FilterTypes.COLUMN_VALUE,
                                                          column=column,
                                                          column_value=column_value)
    if results:
        adv_instance: Advertisement = results[0]
        return adv_instance
    raise HttpError(status_code=404, description=f"Entry is not found.")


def search_advs_by_text(column: AdvertisementColumns,
                        column_value: str | int | datetime,
                        page: int,
                        per_page: int,
                        session) -> dict[str, int | list[dict[str, str]]]:
    filter_object = filtering.Filter(session=session)
    result: dict[str, int | list[ModelClass]] = filter_object.paginate(model_class=Advertisement,
                                                                       filter_type=FilterTypes.SEARCH_TEXT,
                                                                       column=column,
                                                                       column_value=column_value,
                                                                       page=page,
                                                                       per_page=per_page)
    result["items"] = [{item.title: item.description} for item in result["items"]]  # type: ignore
    return result


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
