from typing import Type, TypeVar

from flask import request, jsonify, Response
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError

from app import adv
from app.error_handlers import HttpError
from app import models


@adv.before_request
def before_request() -> None:
    session = models.Session()
    request.session = session


@adv.after_request
def after_request(response: Response) -> Response:
    request.session.close()
    return response


ModelClass = TypeVar("ModelClass", bound=models.Base)


def get_model_instance(model_class: Type[ModelClass], instance_id: int) -> ModelClass:
    model_instance = request.session.get(model_class, instance_id)
    if model_instance is None:
        raise HttpError(404, "not found")
    return model_instance


def add_model_instance(model_instance: ModelClass) -> ModelClass:
    try:
        request.session.add(model_instance)
        request.session.commit()
    except IntegrityError as err:
        raise HttpError(409, f"{str(err)}")
    return model_instance


class UserView(MethodView):

    def session(self) -> models.Session:
        return request.session

    def get(self):
        pass

    def post(self):
        pass

    def patch(self):
        pass

    def delete(self):
        pass


class AdvView(MethodView):

    @property
    def session(self) -> models.Session:
        return request.session

    def get(self, adv_id: int):
        adv: models.Advertisement = get_model_instance(model_class=models.Advertisement, instance_id=adv_id)
        return jsonify(
            {
                "id": adv.id,
                "title": adv.title,
                "description": adv.description,
                "creation_date": adv.creation_date.isoformat(),
                "author": adv.author
            }
        )

    def post(self):
        adv_data = request.json
        new_adv = models.Advertisement(**adv_data)
        add_model_instance(model_instance=new_adv)
        # self.session.add(new_adv)
        # self.session.commit()
        return jsonify({'id': new_adv.id})

    def patch(self, adv_id: int):
        adv = get_model_instance(model_class=models.Advertisement, instance_id=adv_id)
        adv_data = request.json
        for key, value in adv_data.items():
            setattr(adv, key, value)
        adv = add_model_instance(model_instance=adv)
        return jsonify(
            {
                "modified data":
                    {
                        "id": adv.id,
                        "title": adv.title,
                        "description": adv.description,
                        "creation_date": adv.creation_date.isoformat(),
                        "author": adv.author
                    }
            }
        )

    def delete(self, adv_id: int):
        adv = get_model_instance(model_class=models.Advertisement, instance_id=adv_id)
        adv_params = {
            "id": adv.id,
            "title": adv.title,
            "description": adv.description,
            "creation_date": adv.creation_date,
            "author": adv.author
        }
        self.session.delete(adv)
        self.session.commit()
        return jsonify({"deleted": adv_params})


