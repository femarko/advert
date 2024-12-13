from datetime import datetime

import flask
import sqlalchemy.orm
from flask import request, jsonify
from flask_jwt_extended import jwt_required

import app.authentication
from app import adv, models, pass_hashing, validation, service_layer, authentication, filtering
from app.error_handlers import HttpError
from app.models import ModelClass


#  todo: whether all urls have authorization check: if user_id == authentication.get_authenticated_user_identity(): ...
#  todo: put all HttpErrors in views.py


@adv.route("/users/<int:user_id>/", methods=["GET"])
@jwt_required()
def get_user_data(user_id: int) -> tuple[dict[str, int | str | datetime], int]:
    current_user_id: int = authentication.check_current_user(user_id=user_id)
    user: models.User = service_layer.get_user(
        column="id",  # type: ignore
        column_value=current_user_id,
        session=request.session
    )
    return user.get_user_data(), 200


@adv.route("/users/", methods=["POST"])
def create_user():
    validated_data = validation.validate_data(validation_model=validation.CreateUser, data=request.json)
    validated_data["password"] = pass_hashing.hash_password(password=validated_data["password"])
    new_user: models.User = service_layer.add_model_instance(model_instance=models.User(**validated_data))
    new_user_id: int = new_user.id
    return jsonify({"user id": new_user_id}), 201


@adv.route("/users/<int:user_id>/", methods=["PATCH"])
@jwt_required()
def update_user(user_id: int):
    current_user_id: int = authentication.check_current_user(user_id=user_id)
    validated_data = validation.validate_data(validation_model=validation.EditUser, data=request.json)
    user: models.User = service_layer.get_user(
        column="id",  # type: ignore
        column_value=current_user_id,
        session=request.session
    )
    if user:
        updated_user = service_layer.edit_model_instance(model_instance=user, new_data=validated_data)
        return jsonify({"modified user data": updated_user.get_user_data()}), 200


@adv.route("/users/<int:user_id>/advertisements", methods=["GET"])
@jwt_required()
def get_related_advs(user_id: int):
    current_user_id: int = authentication.check_current_user(user_id=user_id)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    result: dict[str, int | list[models.Advertisement]] = service_layer.get_related_advs(
        current_user_id=current_user_id,
        page=page,
        per_page=per_page,
        session=request.session
    )
    return result, 200


@adv.route("/users/<int:user_id>/", methods=["DELETE"])
@jwt_required()
def delete_user(user_id: int):
    current_user_id: int = authentication.check_current_user(user_id=user_id)
    deleted_user = service_layer.get_user(
        column="id",  # type: ignore
        column_value=current_user_id,
        session=request.session
    )
    service_layer.delete_model_instance(deleted_user)
    return jsonify({"deleted user data": deleted_user.get_user_data()}), 200


@adv.route("/advertisements/<int:adv_id>/", methods=["GET"])
@jwt_required()
def get_adv_params(adv_id: int):
    adv_instance: models.Advertisement = service_layer.get_adv(
        column="id",  # type: ignore
        column_value=adv_id,
        session=request.session
    )
    authentication.check_current_user(user_id=adv_instance.user_id, get_cuid=False)
    return jsonify(adv_instance.get_adv_params()), 200


@adv.route("/advertisements/", methods=["POST"])
@jwt_required()
def create_adv():
    validated_data: dict[str, str] = validation.validate_data(validation_model=validation.CreateAdv, data=request.json)
    current_user_id: int = authentication.check_current_user()
    validated_data = validated_data | {"user_id": current_user_id}
    new_adv: models.Advertisement = \
        service_layer.add_model_instance(model_instance=models.Advertisement(**validated_data))
    return jsonify({'advertisement id': new_adv.id}), 201


# todo: do I need this endpoint?
# @adv.route("/advertisements/<int:adv_id>/user", methods=["GET"])
# @jwt_required()
# def get_related_user(adv_id: int):
#     advertisement: models.Advertisement = service_layer.get_related_models(model_class=models.Advertisement,
#                                                                            instance_id=adv_id)
#     return advertisement.get_related_user(), 200


@adv.route("/advertisements/<int:adv_id>/", methods=["PATCH"])
@jwt_required()
def update_adv(adv_id: int):
    adv_instance: models.Advertisement = service_layer.get_adv(
        column="id",  # type: ignore
        column_value=adv_id,
        session=request.session
    )
    authentication.check_current_user(user_id=adv_instance.user_id, get_cuid=False)
    validated_data: dict[str, str | int] = validation.validate_data(validation_model=validation.EditAdv,
                                                                    data=request.json)
    updated_adv = service_layer.edit_model_instance(model_instance=adv_instance, new_data=validated_data)
    return jsonify({"modified advertisement params": updated_adv.get_adv_params()}), 200


@adv.route("/advertisements", methods=["GET"])
def search_advs_by_text():
    data = request.args.to_dict()
    validated_data = validation.validate_data(validation_model=validation.FilterAdvertisement, data=data)
    page = request.args.get("page", 1, type=int)  # todo: add validation
    per_page = request.args.get("per_page", 10, type=int)  # todo: add validation
    result: dict[str, int | list[ModelClass]] = \
        service_layer.search_advs_by_text(column=validated_data["column"],  # type: ignore
                                          column_value=validated_data["column_value"],
                                          page=page,
                                          per_page=per_page,
                                          session=request.session)
    return result, 200


@adv.route("/advertisements/<int:adv_id>/", methods=["DELETE"])
@jwt_required()
def delete_adv(adv_id: int):
    adv_instance = service_layer.get_adv(
        column="id",  # type: ignore
        column_value=adv_id,
        session=request.session
    )
    authentication.check_current_user(user_id=adv_instance.user_id, get_cuid=False)
    service_layer.delete_model_instance(model_instance=adv_instance)
    return jsonify({"deleted advertisement params": adv_instance.get_adv_params()}), 200


@adv.route("/login/", methods=["POST"])
def login():
    validated_data: dict[str, str] = validation.validate_data(validation_model=validation.Login, data=request.json)
    user: models.User = service_layer.get_user(
        column="email",  # type: ignore
        column_value=validated_data["email"],
        session=request.session
    )
    if not user:
        raise HttpError(status_code=401, description="Incorrect email or password")
    if pass_hashing.check_password(password=validated_data["password"], hashed_password=user.password):
        access_token: str = authentication.get_access_token(identity=user.id)
        return jsonify({"access_token": access_token}), 200
    raise HttpError(status_code=401, description="Incorrect email or password")
