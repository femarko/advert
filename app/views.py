from flask import request, jsonify, Response
from flask.views import MethodView
from sqlalchemy.exc import IntegrityError

from app import adv
from app.error_handlers import HttpError
from app.models import Session, Adv


class AdvView(MethodView):

    @property
    def session(self) -> Session:
        return request.session

    def get(self, adv_id: int):
        adv = get_adv(adv_id)
        return jsonify(
            {
                "id": adv.id,
                "title": adv.title,
                "description": adv.description,
                "creation_date": adv.creation_date.isoformat(),
                "author": adv.author
            }
        )

    # @adv.route("/adv", methods=["POST"])
    def post(self):
        adv_data = request.json
        new_adv = Adv(**adv_data)
        self.session.add(new_adv)
        self.session.commit()
        return jsonify({'id': new_adv.id})

    def patch(self, adv_id: int):
        adv = get_adv(adv_id)
        adv_data = request.json
        for key, value in adv_data.items():
            setattr(adv, key, value)
        adv = add_adv(adv)
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
        adv = get_adv(adv_id)
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


def get_adv(adv_id: int):
    adv = request.session.get(Adv, adv_id)
    if adv is None:
        raise HttpError(404, "advertisement not found")
    return adv


def add_adv(adv: Adv):
    try:
        request.session.add(adv)
        request.session.commit()
    except IntegrityError as err:
        raise HttpError(409, "advertisement already exists")
    return adv


@adv.before_request
def before_request() -> None:
    session = Session()
    request.session = session


@adv.after_request
def after_request(response: Response) -> Response:
    request.session.close()
    return response
