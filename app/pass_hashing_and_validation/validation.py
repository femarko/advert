import pydantic
from typing import TypeVar, Type

import app.domain.errors


PydanticModel = TypeVar("PydanticModel", bound=pydantic.BaseModel)


class CreateUser(pydantic.BaseModel):
    name: str
    email: str
    password: str


class UpdateUser(pydantic.BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None


class CreateAdv(pydantic.BaseModel):
    title: str
    description: str


class EditAdv(pydantic.BaseModel):
    title: str | None = None
    description: str | None = None


class Login(pydantic.BaseModel):
    email: str
    password: str


def validate_data(validation_model: Type[PydanticModel], data: dict[str, str]):
    try:
        return validation_model.model_validate(data).model_dump(exclude_unset=True)
    except pydantic.ValidationError as e:
        raise app.domain.errors.ValidationError(e.errors())


def validate_login_credentials(**credentials):
    return validate_data(validation_model=Login, data={**credentials})


def validate_data_for_user_creation(**user_data):
    return validate_data(validation_model=CreateUser, data={**user_data})


def validate_data_for_user_updating(**user_data):
    return validate_data(validation_model=UpdateUser, data={**user_data})


def validate_data_for_adv_creation(**adv_params):
    return validate_data(validation_model=CreateAdv, data={**adv_params})


def validate_data_for_adv_updating(**adv_params):
    return validate_data(validation_model=EditAdv, data={**adv_params})
