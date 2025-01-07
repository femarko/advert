from datetime import datetime

from flask import request, Response
from sqlalchemy.exc import IntegrityError

from app import models, adv
from app.error_handlers import HttpError
from app.repository.filtering import filter_and_return_list, filter_and_return_paginated_data, FilterResult

import logging

from app.models import ModelClass, User, Advertisement
from app.repository.filtering import FilterTypes, UserColumns, AdvertisementColumns, Comparison
from app.repository.repository import Repository
from app.unit_of_work import UnitOfWork

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


def get_user(column: UserColumns, column_value: str | int | datetime, session) -> FilterResult:
    results: FilterResult = filter_and_return_list(session=session,
                                                   model_class=User,
                                                   filter_type=FilterTypes.COLUMN_VALUE,
                                                   comparison=Comparison.IS,
                                                   column=column,
                                                   column_value=column_value)
    return results


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
