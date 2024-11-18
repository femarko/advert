from datetime import datetime
from typing import TypeVar, Type

from flask import request, Response
from sqlalchemy import text, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from app import models, adv
from app.error_handlers import HttpError

import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

ModelClass = TypeVar("ModelClass", bound=models.Base)


@adv.before_request
def before_request() -> None:
    session = models.Session()
    request.session = session


@adv.after_request
def after_request(response: Response) -> Response:
    request.session.close()
    return response


def get_model_instance(model_class: Type[ModelClass], instance_id: int) -> ModelClass:
    model_instance = request.session.get(model_class, instance_id)
    if model_instance is None:
        raise HttpError(status_code=404, description=f"entry with id={instance_id} is not found")
    return model_instance


def retrieve_model_instance(model_class: Type[ModelClass],
                            filter_params: dict[str, str | int | datetime],
                            session) -> list[ModelClass]:

    model_instances: list[ModelClass] = session.query(model_class).filter_by(**filter_params).all()
    return model_instances


def get_related_models(model_class: Type[ModelClass], instance_id: int) -> ModelClass:
    model_instance_with_related_objects: ModelClass = \
        request.session.query(model_class).filter(model_class.id == instance_id).options(joinedload("*")).first()
    return model_instance_with_related_objects


def search_text(table: str, column: str, term: str) -> list[dict[str, str | int | datetime]]:
    stmt = text(f"SELECT * FROM {table} WHERE {column} LIKE '%{term}%'")
    results: list[tuple[str]] = request.session.execute(stmt).all()
    if table == "adv":
        return [{"title": result[1], "description": result[2]} for result in results]
    return results


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
