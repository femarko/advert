import pytest

from app import validation
from app.error_handlers import HttpError


@pytest.mark.parametrize(
    "input_data, missed_field, validation_model",
    (
        ({"email": "test@email.com", "password": "test_password"}, "name", validation.CreateUser),
        ({"name": "test_name", "password": "test_password"}, "email", validation.CreateUser),
        ({"name": "test_name", "email": "test@email.com"}, "password", validation.CreateUser),
        ({"title": "test_title", "description": "test_description"}, "user_id", validation.CreateAdv),
        ({"title": "test_title", "user_id": "test_author"}, "description", validation.CreateAdv),
        ({"description": "test_description", "user_id": "test_author"}, "title", validation.CreateAdv)
    )
)
def test_validate_data_if_incomplete_data_is_provided(input_data, missed_field, validation_model):
    with pytest.raises(HttpError) as exc_info:
        validation.validate_data(validation_model=validation_model, data=input_data)
    assert exc_info.type is HttpError
    assert exc_info.value.args[0] == 400
    assert exc_info.value.args[1][0]["input"] == input_data
    assert exc_info.value.args[1][0]["loc"][0] == missed_field
    assert exc_info.value.args[1][0]["msg"] == "Field required"
    assert exc_info.value.args[1][0]["type"] == "missing"
    assert exc_info.value.args[1][0]["url"] == "https://errors.pydantic.dev/2.9/v/missing"


def test_validate_data_returns_input_data_if_correct_data_is_provided():
    input_data = {"name": "test_name", "email": "test@email.com", "password": "test_pass"}
    validation_result = validation.validate_data(validation_model=validation.CreateUser, data=input_data)
    assert validation_result == input_data

