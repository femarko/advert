from typing import Callable, Any, Type

from flask import request, jsonify, Response
from flask_jwt_extended import jwt_required

from app import adv, models, pass_hashing, validation, service_layer, authentication
from app.error_handlers import HttpError
from app.repository.filtering import FilterResult
from app.models import Advertisement, User

#  todo: whether all urls have authorization check: if user_id == authentication.get_authenticated_user_identity(): ...
#  todo: put all HttpErrors in views.py
#  todo: process validation_result.validation_errors
from app.validation import ValidationResult, PydanticModel


def get_validation_result(validation_func: Callable[[Type[PydanticModel], dict[str, str]], ValidationResult],
                          validation_model: Type[PydanticModel],
                          data: dict[str, str]):
    validation_result = validation_func(validation_model, data)
    if validation_result.status == "OK":
        return validation_result.validated_data
    else:
        raise HttpError(status_code=400, description=validation_result.validation_errors)


def get_filter_result(filter_func: Callable[..., FilterResult], **params: Any):
    filter_result = filter_func(**params)
    if filter_result.status == "OK":
        return filter_result.filtered_data
    raise HttpError(status_code=400, description=filter_result.errors)


@adv.route("/users/<int:user_id>/", methods=["GET"])
@jwt_required()
def get_user_data(user_id: int) -> tuple[Response, int]:
    current_user_id: int = authentication.check_current_user(user_id=user_id)
    user_list: list[User] = get_filter_result(filter_func=service_layer.get_user,
                                              column="id",
                                              column_value=current_user_id,
                                              session=request.session)
    if user_list:
        return jsonify(user_list[0].get_user_data()), 200
    raise HttpError(status_code=404, description=f"User with {current_user_id=} is not found.")


@adv.route("/users/", methods=["POST"])
def create_user():
    validated_data = get_validation_result(validation_func=validation.validate_data,
                                           validation_model=validation.CreateUser,
                                           data=request.json)
    validated_data["password"] = pass_hashing.hash_password(password=validated_data["password"])
    new_user: models.User = service_layer.add_model_instance(model_instance=models.User(**validated_data))
    new_user_id: int = new_user.id
    return jsonify({"user id": new_user_id}), 201


@adv.route("/users/<int:user_id>/", methods=["PATCH"])
@jwt_required()
def update_user(user_id: int):
    current_user_id: int = authentication.check_current_user(user_id=user_id)
    validated_data = get_validation_result(validation_func=validation.validate_data,
                                           validation_model=validation.EditUser,
                                           data=request.json)
    user_list: list[User] = get_filter_result(filter_func=service_layer.get_user,
                                              column="id",
                                              column_value=current_user_id,
                                              session=request.session)
    if user_list:
        updated_user = service_layer.edit_model_instance(model_instance=user_list[0], new_data=validated_data)
        return jsonify({"modified user data": updated_user.get_user_data()}), 200
    raise HttpError(status_code=404, description=f"User with {validated_data['id']=} is not found.")


@adv.route("/users/<int:user_id>/advertisements", methods=["GET"])
@jwt_required()
def get_related_advs(user_id: int):
    current_user_id: int = authentication.check_current_user(user_id=user_id)
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)
    result = get_filter_result(filter_func=service_layer.get_related_advs,
                               current_user_id=current_user_id,
                               page=page,
                               per_page=per_page,
                               session=request.session)
    result["items"] = [item.get_adv_params() for item in result["items"]]
    return result


@adv.route("/users/<int:user_id>/", methods=["DELETE"])
@jwt_required()
def delete_user(user_id: int):
    current_user_id: int = authentication.check_current_user(user_id=user_id)
    filter_result: FilterResult = service_layer.get_user(
        column="id", column_value=current_user_id, session=request.session  # type: ignore
    )
    if filter_result.status == "OK":
        if filter_result.filtered_data:
            user: User = filter_result.filtered_data[0]
            service_layer.delete_model_instance(model_instance=user)
            return jsonify({"deleted user data": user.get_user_data()}), 200
        raise HttpError(status_code=404, description=f"User with {current_user_id=} is not found.")
    raise HttpError(status_code=400, description=filter_result.errors)


@adv.route("/advertisements/<int:adv_id>/", methods=["GET"])
@jwt_required()
def get_adv_params(adv_id: int):
    filter_result: FilterResult = service_layer.get_adv(
        column="id", column_value=adv_id, session=request.session  # type: ignore
    )
    if filter_result.status == "OK":
        if filter_result.filtered_data:
            adv_instance: Advertisement = filter_result.filtered_data[0]
            authentication.check_current_user(user_id=adv_instance.user_id, get_cuid=False)
            return jsonify(adv_instance.get_adv_params()), 200
        raise HttpError(status_code=404, description=f"Advertisement with {adv_id=} is not found.")
    raise HttpError(status_code=400, description=filter_result.errors)


@adv.route("/advertisements/", methods=["POST"])
@jwt_required()
def create_adv():
    validation_result: ValidationResult = validation.validate_data(validation_model=validation.CreateAdv,
                                                                   data=request.json)
    validated_data = validation_result.validated_data
    current_user_id: int = authentication.check_current_user()
    validated_data |= {"user_id": current_user_id}
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
    filter_result: FilterResult = service_layer.get_adv(
        column="id", column_value=adv_id, session=request.session  # type: ignore
    )
    if filter_result.status == "OK":
        if filter_result.filtered_data:
            authentication.check_current_user(user_id=filter_result.filtered_data[0].user_id, get_cuid=False)
            validation_result: ValidationResult = validation.validate_data(validation_model=validation.EditAdv,
                                                                           data=request.json)
            validated_data = validation_result.validated_data
            updated_adv = service_layer.edit_model_instance(model_instance=filter_result.filtered_data[0],
                                                            new_data=validated_data)
            return jsonify({"modified advertisement params": updated_adv.get_adv_params()}), 200
        raise HttpError(status_code=404, description=f"Advertisement with {adv_id=} is not found.")
    raise HttpError(status_code=400, description=filter_result.errors)


@adv.route("/advertisements", methods=["GET"])
def search_advs_by_text():
    # data = request.args.to_dict()
    # validation_result: ValidationResult = validation.validate_data(validation_model=validation.FilterAdvertisement,
    #                                                                data=data)
    # validated_data = validation_result.validated_data
    page = request.args.get("page", 1, type=int)  # todo: add validation
    per_page = request.args.get("per_page", 10, type=int)  # todo: add validation
    filter_result: FilterResult = service_layer.search_advs_by_text(column=request.args.get("column"),  # type: ignore
                                                                    column_value=request.args.get("column_value"),
                                                                    page=page,
                                                                    per_page=per_page,
                                                                    session=request.session)
    if filter_result.status == "OK":
        return filter_result.filtered_data, 200
    raise HttpError(status_code=400, description=filter_result.errors)


@adv.route("/advertisements/<int:adv_id>/", methods=["DELETE"])
@jwt_required()
def delete_adv(adv_id: int):
    filter_result: FilterResult = service_layer.get_adv(
        column="id", column_value=adv_id, session=request.session  # type: ignore
    )
    if filter_result.status == "OK":
        if filter_result.filtered_data:
            adv_instance: Advertisement = filter_result.filtered_data[0]
            authentication.check_current_user(user_id=adv_instance.user_id, get_cuid=False)
            service_layer.delete_model_instance(model_instance=adv_instance)
            return jsonify({"deleted advertisement params": adv_instance.get_adv_params()}), 200
        raise HttpError(status_code=404, description=f"Advertisement with {adv_id=} is not found.")
    raise HttpError(status_code=400, description=filter_result.errors)


@adv.route("/login/", methods=["POST"])
def login():
    validation_result: ValidationResult = validation.validate_data(validation_model=validation.Login, data=request.json)
    validated_data = validation_result.validated_data
    filter_result: FilterResult = service_layer.get_user(
        column="email", column_value=validated_data["email"], session=request.session  # type: ignore
    )
    if filter_result.status == "OK":
        if filter_result.filtered_data:
            user: User = filter_result.filtered_data[0]
            if pass_hashing.check_password(password=validated_data["password"], hashed_password=user.password):
                access_token: str = authentication.get_access_token(identity=user.id)
                return jsonify({"access_token": access_token}), 200
            raise HttpError(status_code=401, description="Incorrect email or password")
        raise HttpError(status_code=401, description=f"Incorrect email or password")
    raise HttpError(status_code=400, description=filter_result.errors)
