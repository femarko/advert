import pytest

from app.validation import validate_data, CreateAdv, CreateUser, Login
from app.error_handlers import HttpError


@pytest.mark.parametrize(
    "input_data, missed_field, validation_model",
    (
        ({"email": "test@email.com", "password": "test_password"}, "name", CreateUser),
        ({"name": "test_name", "password": "test_password"}, "email", CreateUser),
        ({"name": "test_name", "email": "test@email.com"}, "password", CreateUser),
        ({"title": "test_title", "user_id": "test_author"}, "description", CreateAdv),
        ({"description": "test_description", "user_id": "test_author"}, "title", CreateAdv),
        ({"email": "test_2@email.com"}, "password", Login),
        ({"password": "test_2@email.com"}, "email", Login)
    )
)
def test_validate_data_if_incomplete_data_is_provided(input_data, missed_field, validation_model):
    with pytest.raises(HttpError) as exc_info:
        validate_data(validation_model=validation_model, data=input_data)
    assert exc_info.type is HttpError
    assert exc_info.value.args[0] == 400
    assert exc_info.value.args[1][0]["input"] == input_data
    assert exc_info.value.args[1][0]["loc"][0] == missed_field
    assert exc_info.value.args[1][0]["msg"] == "Field required"
    assert exc_info.value.args[1][0]["type"] == "missing"
    assert exc_info.value.args[1][0]["url"] == "https://errors.pydantic.dev/2.9/v/missing"


# @pytest.mark.parametrize(  # todo: test_validate_data_if_incorrect_data_is_provided
#     "input_data, incorrect_field, validation_model",
#     (
#         ({"incorrect_field": "value", "email": "test@email.com", "password": "test_password"}, "name", CreateUser),
#         ({"name": "test_name", "password": "test_password"}, "email", CreateUser),
#         ({"name": "test_name", "email": "test@email.com"}, "password", CreateUser),
#         ({"title": "test_title", "description": "test_description"}, "user_id", CreateAdv),
#         ({"title": "test_title", "user_id": "test_author"}, "description", CreateAdv),
#         ({"description": "test_description", "user_id": "test_author"}, "title", CreateAdv),
#         ({"email": "test_2@email.com", "password": True}, "password", Login),
#     )
# )
# def test_validate_data_if_incorrect_data_is_provided(input_data, incorrect_field, validation_model):
#     with pytest.raises(HttpError) as exc_info:
#         validate_data(validation_model=validation_model, data=input_data)
#     assert exc_info.type is HttpError
#     assert exc_info.value.args[0] == 400
#     assert exc_info.value.args[1][0]["input"] in (input_data, input_data[incorrect_field])
#     assert exc_info.value.args[1][0]["loc"][0] == incorrect_field
#     assert exc_info.value.args[1][0]["msg"] in ("Field required", "Input should be a valid string")
#     assert exc_info.value.args[1][0]["type"] in ("missing", "string_type")
#     assert exc_info.value.args[1][0]["url"] in ("https://errors.pydantic.dev/2.9/v/missing",
#                                                 "https://errors.pydantic.dev/2.9/v/string_type")


def test_validate_data_returns_input_data_if_correct_data_is_provided():
    input_data = {"name": "test_name", "email": "test@email.com", "password": "test_pass"}
    validation_result = validate_data(validation_model=CreateUser, data=input_data)
    assert validation_result == input_data

