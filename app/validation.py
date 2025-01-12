import pydantic
from typing import TypeVar, Type, Any, Literal
from dataclasses import dataclass

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


class EditAdv(pydantic.BaseModel):
    title: str | None = None
    description: str | None = None
    user_id: int | None = None


class Login(pydantic.BaseModel):
    email: str
    password: str


@dataclass
class ValidationResult:
    result: dict[Any, Any] | None = None
    errors: list[str] | None = None


def validate_data(validation_model: Type[PydanticModel], data: dict[str, str]) -> ValidationResult:
    try:
        return ValidationResult(result=validation_model.model_validate(data).model_dump(exclude_unset=True))
    except pydantic.ValidationError as e:
        errors_list: list = e.errors()
        return ValidationResult(errors=errors_list)


def validate_login_credentials(**credentials):
    return validate_data(validation_model=Login, data={**credentials})


def validate_user_data(**user_data):
    return validate_data(validation_model=CreateUser, data={**user_data})

