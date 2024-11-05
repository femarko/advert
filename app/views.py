from flask import request, jsonify

from app import adv, models, pass_hashing, validation, service_layer
from app.error_handlers import HttpError


@adv.route("/users/<int:user_id>/", methods=["GET"])
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
def update_user(user_id: int):
    validated_data = validation.validate_data(validation_model=validation.EditUser, data=request.json)
    user = service_layer.get_model_instance(model_class=models.User, instance_id=user_id)
    HttpError(status_code=404, description=f'user with id = {user_id} not found')
    updated_user = service_layer.edit_model_instance(model_instance=user, new_data=validated_data)
    return {"modified user data": updated_user.get_user_data()}, 200


@adv.route("/users/<int:user_id>/advertisements/", methods=["GET"])
def get_related_advs(user_id: int):
    user: models.User = service_layer.get_related_models(model_class=models.User, instance_id=user_id)
    return user.get_user_advs(), 200


@adv.route("/users/<int:user_id>/", methods=["DELETE"])
def delete_user(user_id: int):
    deleted_user = service_layer.get_model_instance(model_class=models.User, instance_id=user_id)
    service_layer.delete_model_instance(deleted_user)
    return jsonify({"deleted user data": deleted_user.get_user_data()}), 200


@adv.route("/advertisements/<int:adv_id>/", methods=["GET"])
def get_adv_params(adv_id: int):
    adv: models.Advertisement = service_layer.get_model_instance(model_class=models.Advertisement, instance_id=adv_id)
    return jsonify(adv.get_adv_params()), 200


@adv.route("/advertisements/", methods=["POST"])
def create_adv():
    validated_data = validation.validate_data(validation_model=validation.CreateAdv, data=request.json)
    new_adv = service_layer.add_model_instance(model_instance=models.Advertisement(**validated_data))
    return jsonify({'advertisement id': new_adv.id}), 201


@adv.route("/advertisements/<int:adv_id>/user", methods=["GET"])
def get_related_user(adv_id: int):
    advertisement: models.Advertisement = service_layer.get_related_models(model_class=models.Advertisement,
                                                                           instance_id=adv_id)
    return advertisement.get_related_user(), 200


@adv.route("/advertisements/<int:adv_id>/", methods=["PATCH"])
def update_adv(adv_id: int):
    validated_data = validation.validate_data(validation_model=validation.EditAdv, data=request.json)
    adv = service_layer.get_model_instance(model_class=models.Advertisement, instance_id=adv_id)
    updated_adv = service_layer.edit_model_instance(model_instance=adv, new_data=validated_data)
    return jsonify({"modified advertisement params": updated_adv.get_adv_params()}), 200


@adv.route("/advertisements/<int:adv_id>/", methods=["DELETE"])
def delete_adv(adv_id: int):
    deleted_adv = service_layer.get_model_instance(model_class=models.Advertisement, instance_id=adv_id)
    service_layer.delete_model_instance(deleted_adv)
    return jsonify({"deleted advertisement params": deleted_adv.get_adv_params()}), 200
