from typing import TypeVar, Type

from flask import request, Response
from sqlalchemy.exc import IntegrityError

from app import models, adv
from app.error_handlers import HttpError

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
