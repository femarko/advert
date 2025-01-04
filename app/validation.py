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


# class FilterAdvertisement(pydantic.BaseModel):
#     model_class: Advertisement
#     filter_type: FilterTypes
#     comparison: Comparison | None = None
#     column: AdvertisementColumns
#     column_value: str | int | datetime


# class FilterUser(pydantic.BaseModel):
#     model_class: Model.USER
#     filter_type: FilterTypes
#     comparison: Comparison | None = None
#     column: UserColumns
#     column_value: str | int | datetime


# class FilterParams(pydantic.BaseModel):
#     model_class: Model
#     filter_type: FilterTypes
#     comparison: Comparison | None = None
#     column: UserColumns | AdvertisementColumns
#     column_value: str | int | datetime
#     page: int | str
#     per_page: int | str


@dataclass
class ValidationResult:
    validated_data: dict[Any, Any] | None = None
    validation_errors: list[str] | None = None
    status: Literal["OK", "Failed"] = "OK"


def validate_data(validation_model: Type[PydanticModel], data: dict[str, str]) -> ValidationResult:
    try:
        return ValidationResult(validated_data=validation_model.model_validate(data).model_dump(exclude_unset=True))
    except pydantic.ValidationError as err:
        errors_list: list = err.errors()
        return ValidationResult(status="Failed", validation_errors=errors_list)
