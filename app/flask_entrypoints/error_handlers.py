from flask import jsonify

from app.flask_entrypoints import adv


class HttpError(Exception):
    def __init__(self, status_code: int, description: str | list | set):
        self.status_code = status_code
        self.description = description


@adv.errorhandler(HttpError)
def error_handler(error):
    response = jsonify({"errors": error.description})
    response.status_code = error.status_code
    return response
