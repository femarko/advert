import flask
from flask import jsonify, request, Response
from flask.views import MethodView
from flask import Response
from models import Session, Adv
from sqlalchemy.exc import IntegrityError


adv = flask.Flask('adv')


class HttpError(Exception):
    def __init__(self, status_code: int, description: str):
        self.status_code = status_code
        self.description = description

@adv.errorhandler(HttpError)
def error_handler(error):
    response = jsonify({"error": error.description})
    response.status_code = error.status_code
    return response


@adv.before_request
def before_request():
    session = Session()
    request.session = session


@adv.after_request
def after_request(response: Response):
    request.session.close()
    return response


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
        raise HttpError(409,"advertisement already exists")
    return adv


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


adv_view = AdvView.as_view("adv_view")
adv.add_url_rule("/adv/<int:adv_id>", view_func=adv_view, methods=["GET", "PATCH", "DELETE"])
adv.add_url_rule("/adv", view_func=adv_view, methods=["POST"])

if __name__ == "__main__":
    adv.run(debug=True)
