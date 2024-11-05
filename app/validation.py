import pydantic
from typing import TypeVar, Type

from app.error_handlers import HttpError


PydanticModel = TypeVar("PydanticModel", bound=pydantic.BaseModel)


class CreateUser(pydantic.BaseModel):
    name: str
    email: str
    password: str


class EditUser(pydantic.BaseModel):
    name: str | None = None
    email: str | None = None
    password: str | None = None



class CreateAdv(pydantic.BaseModel):
    title: str
    description: str
    user_id: int


class EditAdv(pydantic.BaseModel):
    title: str | None = None
    description: str | None = None
    user_id: int | None = None


def validate_data(validation_model: Type[PydanticModel], data: dict[str, str]) -> dict[str, str] | None:
    try:
        return validation_model.model_validate(data).model_dump(exclude_unset=True)
    except pydantic.ValidationError as err:
        errors_list: list = err.errors()
        raise HttpError(400, errors_list)
