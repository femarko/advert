import dataclasses
import datetime
from typing import cast, Any, Optional

import sqlalchemy, pytest

import app.errors
from app import pass_hashing, authentication, unit_of_work, validation, models, services
import app.authentication
from app import service_layer

# @pytest.mark.run(order=9)
# def test_current_user_is_authorized(access_token):
#     fake_user_id = 1
#     app.authentication.check_current_user(user_id=fake_user_id)
#     assert ...
#
#
# def test_get_user(session_maker):
#     session = session_maker
#     email = "test_1@email.com"
#     with session() as sess:
#         filter_result: FilterResult = service_layer.get_users_list(
#             column="email", column_value=email, session=sess  # type: ignore
#         )
#     with session() as sess:
#         expected = sess \
#             .execute(sqlalchemy.text(f'SELECT * FROM "user" WHERE email = :email'), dict(email=email)).first()
#     assert filter_result.result[0].id == expected[0]
#     assert filter_result.result[0].name == expected[1]
#     assert filter_result.result[0].email == expected[2]
#     assert filter_result.result[0].password == expected[3]
#     assert filter_result.result[0].creation_date == expected[4]
from app.models import Advertisement, AdvertisementColumns


@dataclasses.dataclass
class FakeUnitOfWorkWithInstances:
    fake_uow: Any
    user_id: Optional[int] = None
    adv_id: Optional[int] = None


@pytest.fixture(scope="function")
def fake_uow_user_and_adv(
        test_user_data, fake_users_repo, fake_advs_repo, fake_unit_of_work, fake_validate_func, fake_hash_pass_func,
        fake_get_auth_user_id_func, test_adv_params
):
    fake_uow = fake_unit_of_work(users=fake_users_repo(users=[]), advs=fake_advs_repo([]))
    user_id: int = service_layer.create_user(
        user_data=test_user_data, validate_func=fake_validate_func, hash_pass_func=fake_hash_pass_func, uow=fake_uow
    )
    adv_id: int = service_layer.create_adv(
        get_auth_user_id_func=fake_get_auth_user_id_func, validate_func=fake_validate_func, adv_params=test_adv_params,
        uow=fake_uow
    )
    return FakeUnitOfWorkWithInstances(fake_uow=fake_uow, user_id=user_id, adv_id=adv_id)


@pytest.fixture(scope="function")
def fake_uow_user(
        test_user_data, fake_users_repo, fake_advs_repo, fake_unit_of_work, fake_validate_func, fake_hash_pass_func,
        fake_get_auth_user_id_func, test_adv_params
):
    fake_uow = fake_unit_of_work(users=fake_users_repo(users=[]), advs=fake_advs_repo([]))
    user_id: int = service_layer.create_user(
        user_data=test_user_data, validate_func=fake_validate_func, hash_pass_func=fake_hash_pass_func, uow=fake_uow
    )
    return FakeUnitOfWorkWithInstances(fake_uow=fake_uow, user_id=user_id)


def test_get_user_data_returns_200(fake_check_current_user_func, test_date, fake_uow_user_and_adv, test_user_data):
    user_id, fake_uow = fake_uow_user_and_adv.user_id, fake_uow_user_and_adv.fake_uow
    result = service_layer.get_user_data(
        user_id=user_id, check_current_user_func=fake_check_current_user_func, uow=fake_uow
    )
    expected_result = {
        "id": user_id,
        "name": test_user_data["name"],
        "email": test_user_data["email"],
        "creation_date": test_date.isoformat()
    }
    assert result == expected_result


def test_get_user_data_raises_not_found_error(fake_check_current_user_func, fake_users_repo, fake_unit_of_work):
    fake_uow = fake_unit_of_work(users=fake_users_repo([]))
    with pytest.raises(expected_exception=app.errors.NotFoundError) as e:
        service_layer.get_user_data(user_id=1, check_current_user_func=fake_check_current_user_func,uow=fake_uow)
    assert e.value.message == "The user with the provided parameters is not found."


def test_create_user(
        fake_validate_func, fake_hash_pass_func, fake_users_repo, fake_advs_repo, fake_unit_of_work, test_date
):
    user_data = {
        "name": "test_name", "email": "test@email.test", "password": "test_password", "creation_date": test_date
    }
    fuow = fake_unit_of_work(users=fake_users_repo([]), advs=fake_advs_repo([]))
    result = service_layer.create_user(
        user_data=user_data, validate_func=fake_validate_func, hash_pass_func=fake_hash_pass_func,
        uow=fuow
    )
    data_from_repo = fuow.users.instances.pop()
    assert type(result) is int
    assert 0 <= result <= 9
    assert result == data_from_repo.id
    assert data_from_repo.name == user_data["name"]
    assert data_from_repo.email == user_data["email"]
    assert data_from_repo.password == user_data["password"]
    assert data_from_repo.creation_date == user_data["creation_date"]


def test_update_user(
        fake_check_current_user_func, fake_validate_func, fake_hash_pass_func, test_date, fake_uow_user_and_adv
):
    new_data = {"name": "new_name", "email": "new_email", "password": "new_pass"}
    user_id = fake_uow_user_and_adv.user_id
    expected_result = {"id": user_id, "creation_date": test_date.isoformat(), **new_data}
    expected_password = expected_result.pop("password")
    result = service_layer.update_user(
        user_id=user_id, check_current_user_func=fake_check_current_user_func, validate_func=fake_validate_func,
        hash_pass_func=fake_hash_pass_func, new_data=new_data, uow=fake_uow_user_and_adv.fake_uow
    )
    assert result == expected_result
    assert fake_uow_user_and_adv.fake_uow.users.instances.pop().password == expected_password


def test_get_related_advs(fake_check_current_user_func, fake_uow_user_and_adv):
    user_id, adv_id, fake_uow = \
        fake_uow_user_and_adv.user_id, fake_uow_user_and_adv.adv_id, fake_uow_user_and_adv.fake_uow
    result: dict[str, int | list[dict[str, str | int]]] = service_layer.get_related_advs(
        authenticated_user_id=user_id, check_current_user_func=fake_check_current_user_func, uow=fake_uow
    )
    expected: dict[str, str | int] = service_layer.get_adv_params(
        adv_id=adv_id, check_current_user_func=fake_check_current_user_func, uow=fake_uow
    )
    assert result["items"] == [expected]


def test_delete_user(fake_check_current_user_func, fake_uow_user_and_adv):
    user_id, fake_uow = fake_uow_user_and_adv.user_id, fake_uow_user_and_adv.fake_uow
    user_data_before_deletion = service_layer.get_user_data(
        user_id=user_id, check_current_user_func=fake_check_current_user_func, uow=fake_uow
    )
    result = service_layer.delete_user(
        user_id=user_id, check_current_user_func=fake_check_current_user_func, uow=fake_uow
    )
    try:
        service_layer.get_user_data(user_id=user_id, check_current_user_func=fake_check_current_user_func, uow=fake_uow)
    except app.errors.NotFoundError as e:
        assert e.message == "The user with the provided parameters is not found."
    assert result == user_data_before_deletion


def test_delete_user_raises_not_found_error(fake_check_current_user_func, fake_uow_user_and_adv):
    user_id, uow = fake_uow_user_and_adv.user_id, fake_uow_user_and_adv.fake_uow
    with pytest.raises(app.errors.NotFoundError):
        service_layer.delete_user(user_id=user_id + 1, check_current_user_func=fake_check_current_user_func, uow=uow)


def test_create_adv(
        fake_get_auth_user_id_func, fake_validate_func, test_date, fake_uow_user, fake_check_current_user_func
):
    user_id, fake_uow = fake_uow_user.user_id, fake_uow_user.fake_uow
    adv_params = {"title": "test_title", "description": "test_description"}
    result = service_layer.create_adv(get_auth_user_id_func=fake_get_auth_user_id_func, adv_params=adv_params,
                                      validate_func=fake_validate_func, uow=fake_uow)
    data_from_repo = service_layer.get_adv_params(
        adv_id=result, check_current_user_func=fake_check_current_user_func, uow=fake_uow)
    assert isinstance(result, int)
    assert result == data_from_repo["id"]
    assert data_from_repo["title"] == adv_params["title"]
    assert data_from_repo["description"] == adv_params["description"]
    assert data_from_repo["creation_date"] == test_date.isoformat()
    assert data_from_repo["user_id"] == user_id


def test_get_adv_params(fake_check_current_user_func, test_date, fake_uow_user_and_adv, test_adv_params):
    user_id, adv_id, fake_uow = \
        fake_uow_user_and_adv.user_id, fake_uow_user_and_adv.adv_id, fake_uow_user_and_adv.fake_uow
    result = service_layer.get_adv_params(
        adv_id=adv_id, check_current_user_func=fake_check_current_user_func, uow=fake_uow
    )
    expected_result = {"id": adv_id, "user_id": user_id, **test_adv_params}
    assert result["id"] == expected_result["id"]
    assert result["title"] == expected_result["title"]
    assert result["user_id"] == expected_result["user_id"]
    assert result["description"] == expected_result["description"]
    assert result["creation_date"] == test_date.isoformat()


def test_get_adv_params_raises_not_found_error(fake_check_current_user_func, fake_advs_repo, fake_unit_of_work):
    uow = fake_unit_of_work(advs=fake_advs_repo(advs=[]))
    with pytest.raises(expected_exception=app.errors.NotFoundError) as e:
        service_layer.get_adv_params(adv_id=1, check_current_user_func=fake_check_current_user_func, uow=uow)
    assert e.value.message == "The advertisement with the provided parameters is not found."


def test_update_adv(fake_validate_func, fake_check_current_user_func, fake_uow_user_and_adv):
    adv_id, fake_uow = fake_uow_user_and_adv.adv_id, fake_uow_user_and_adv.fake_uow
    new_params = {"title": "new_title", "description": "new_description"}
    result: dict[str, str | int] = service_layer.update_adv(
        adv_id=adv_id, new_params=new_params, check_current_user_func=fake_check_current_user_func,
        validate_func=fake_validate_func, uow=fake_uow
    )
    adv_from_repo_params: dict[str, str | int] = service_layer.get_adv_params(
        adv_id=adv_id, check_current_user_func=fake_check_current_user_func, uow=fake_uow
    )
    assert adv_from_repo_params["title"] == new_params["title"]
    assert adv_from_repo_params["description"] == new_params["description"]
    assert result == adv_from_repo_params


def test_update_adv_raises_not_found_error(fake_validate_func, fake_check_current_user_func, fake_uow_user_and_adv):
    adv_id, fake_uow, new_params = \
        fake_uow_user_and_adv.adv_id + 1, fake_uow_user_and_adv.fake_uow, {"title": "new_title"}
    with pytest.raises(expected_exception=app.errors.NotFoundError) as e:
        service_layer.update_adv(
            adv_id=adv_id, new_params=new_params, check_current_user_func=fake_check_current_user_func,
            validate_func=fake_validate_func, uow=fake_uow_user_and_adv.fake_uow
        )


def test_search_advs_by_text(test_adv_params, fake_uow_user_and_adv):
    fake_uow = fake_uow_user_and_adv.fake_uow
    column_value = "test"
    result: dict[str, str | int] = service_layer.search_advs_by_text(column_value=column_value, uow=fake_uow)
    assert result == {"items": [{test_adv_params["title"]: test_adv_params["description"]}]}


def test_delete_adv(fake_get_auth_user_id_func, fake_uow_user_and_adv, fake_check_current_user_func):
    adv_id, fuow = fake_uow_user_and_adv.adv_id, fake_uow_user_and_adv.fake_uow
    deleted_adv_params: dict[str, str | int] = service_layer.delete_adv(
        adv_id=adv_id, get_auth_user_id_func=fake_get_auth_user_id_func, uow=fuow
    )
    try:
        service_layer.get_adv_params(adv_id=adv_id, check_current_user_func=fake_check_current_user_func, uow = fuow)
    except app.errors.NotFoundError as e:
        assert e.message == "The advertisement with the provided parameters is not found."
    assert deleted_adv_params == {"id": deleted_adv_params["id"],
                                  "title": deleted_adv_params["title"],
                                  "description": deleted_adv_params["description"],
                                  "creation_date": deleted_adv_params["creation_date"],
                                  "user_id": deleted_adv_params["user_id"]}


def test_delete_adv_raises_current_user_error(fake_get_auth_user_id_func_2, fake_uow_user_and_adv):
    adv_id, fake_uow = fake_uow_user_and_adv.adv_id, fake_uow_user_and_adv.fake_uow
    with pytest.raises(expected_exception=app.errors.CurrentUserError) as e:
        service_layer.delete_adv(adv_id=adv_id, get_auth_user_id_func=fake_get_auth_user_id_func_2, uow=fake_uow)
    assert e.value.message == "Unavailable operation."


def test_delete_adv_raises_not_found_error(fake_get_auth_user_id_func, fake_advs_repo, fake_unit_of_work,):
    fake_uow = fake_unit_of_work(advs=fake_advs_repo([]))
    with pytest.raises(expected_exception=app.errors.NotFoundError) as e:
        service_layer.delete_adv(adv_id=1, get_auth_user_id_func=fake_get_auth_user_id_func, uow=fake_uow)
    assert e.value.message == "The advertisement with the provided parameters is not found."
