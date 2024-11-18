from flask import request, jsonify
from flask_jwt_extended import jwt_required
from sqlalchemy import text

from app import adv, models, pass_hashing, validation, service_layer, authentication
from app.error_handlers import HttpError


@adv.route("/users/<int:user_id>/", methods=["GET"])
@jwt_required()
def get_user_data(user_id: int):
    user: models.User = service_layer.get_model_instance(model_class=models.User, instance_id=user_id)
    return user.get_user_data(), 200


@adv.route("/users/", methods=["POST"])
def create_user():
    validated_data = validation.validate_data(validation_model=validation.CreateUser, data=request.json)
    validated_data["password"] = pass_hashing.hash_password(password=validated_data["password"])
    new_user = service_layer.add_model_instance(model_instance=models.User(**validated_data))
    new_user_id = new_user.id
    return jsonify({"user id": new_user_id}), 201


@adv.route("/users/<int:user_id>/", methods=["PATCH"])
@jwt_required()
def update_user(user_id: int):
    validated_data = validation.validate_data(validation_model=validation.EditUser, data=request.json)
    user = service_layer.get_model_instance(model_class=models.User, instance_id=user_id)
    if user:
        updated_user = service_layer.edit_model_instance(model_instance=user, new_data=validated_data)
        return {"modified user data": updated_user.get_user_data()}, 200


@adv.route("/users/<int:user_id>/advertisements/", methods=["GET"])
@jwt_required()
def get_related_advs(user_id: int):
    user: models.User = service_layer.get_related_models(model_class=models.User, instance_id=user_id)
    return user.get_user_advs(), 200


@adv.route("/users/<int:user_id>/", methods=["DELETE"])
@jwt_required()
def delete_user(user_id: int):
    deleted_user = service_layer.get_model_instance(model_class=models.User, instance_id=user_id)
    service_layer.delete_model_instance(deleted_user)
    return jsonify({"deleted user data": deleted_user.get_user_data()}), 200


@adv.route("/advertisements/<int:adv_id>/", methods=["GET"])
@jwt_required()
def get_adv_params(adv_id: int):
    adv: models.Advertisement = service_layer.get_model_instance(model_class=models.Advertisement, instance_id=adv_id)
    return jsonify(adv.get_adv_params()), 200


@adv.route("/advertisements/", methods=["POST"])
@jwt_required()
def create_adv():
    validated_data = validation.validate_data(validation_model=validation.CreateAdv, data=request.json)
    current_user_id: int = authentication.get_jwt_identity()
    adv_params = validated_data | {"user_id": current_user_id}
    new_adv = service_layer.add_model_instance(model_instance=models.Advertisement(**adv_params))
    return jsonify({'advertisement id': new_adv.id}), 201


@adv.route("/advertisements/<int:adv_id>/user", methods=["GET"])
@jwt_required()
def get_related_user(adv_id: int):
    advertisement: models.Advertisement = service_layer.get_related_models(model_class=models.Advertisement,
                                                                           instance_id=adv_id)
    return advertisement.get_related_user(), 200


@adv.route("/advertisements/<int:adv_id>/", methods=["PATCH"])
@jwt_required()
def update_adv(adv_id: int):
    validated_data = validation.validate_data(validation_model=validation.EditAdv, data=request.json)
    adv = service_layer.get_model_instance(model_class=models.Advertisement, instance_id=adv_id)
    updated_adv = service_layer.edit_model_instance(model_instance=adv, new_data=validated_data)
    return jsonify({"modified advertisement params": updated_adv.get_adv_params()}), 200


@adv.route("/advertisements", methods=["GET"])
def search_text():
    result = service_layer.search_text(table="adv", column=request.args.get("column"), term=request.args.get("term"))
    return result, 200


@adv.route("/advertisements/<int:adv_id>/", methods=["DELETE"])
@jwt_required()
def delete_adv(adv_id: int):
    advertisement = service_layer.get_model_instance(model_class=models.Advertisement, instance_id=adv_id)
    if advertisement.user_id == authentication.get_authorized_user_identity():
        deleted_adv = service_layer.get_model_instance(model_class=models.Advertisement, instance_id=adv_id)
        service_layer.delete_model_instance(deleted_adv)
        return jsonify({"deleted advertisement params": deleted_adv.get_adv_params()}), 200
    raise HttpError(status_code=403, description="You are not authorised to delete this advertisement.")


@adv.route("/login/", methods=["POST"])
def login():
    validated_data = validation.validate_data(validation_model=validation.Login, data=request.json)
    user_list: list[models.User] = service_layer.retrieve_model_instance(
        model_class=models.User, filter_params={"email": validated_data["email"]}, session=request.session
    )
    if not user_list:
        raise HttpError(status_code=401, description="Incorrect email or password")
    user: models.User = user_list[0]
    if pass_hashing.check_password(password=validated_data["password"], hashed_password=user.password):
        access_token = authentication.create_access_token(identity=user.id)
        return jsonify({"access_token": access_token}), 200
    raise HttpError(status_code=401, description="Incorrect email or password")
