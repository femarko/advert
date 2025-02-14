from typing import Literal
import pytest
from datetime import datetime

import app.service_layer
from app import pass_hashing, authentication, validation, service_layer, unit_of_work, table_mapper
from app.models import User, Advertisement


@pytest.fixture(scope="function", autouse=True)
def register_urls():
    from app import views


@pytest.fixture
def create_user_through_http(test_client, test_user_data) -> int:
    user_id: int = test_client.post("http://127.0.0.1:5000/users/", json=test_user_data).json
    return user_id


@pytest.fixture
def test_user_id() -> Literal[1]:
    return 1


@pytest.fixture
def access_token(test_client, create_user_through_http, app_context, test_user_data):
    with app_context:
        response = test_client.post("http://127.0.0.1:5000/login/", json=test_user_data)
        access_token = response.json.get("access_token")
    return access_token


@pytest.fixture
def create_adv_through_http(test_adv_params, test_user_id, test_client, access_token) -> int:
    response = test_client.post("http://127.0.0.1:5000/advertisements/", json=test_adv_params,
                                headers={"Authorization": f"Bearer {access_token}"})
    adv_id: int = response.json.get("new_advertisement_id")
    return adv_id


@pytest.fixture
def test_adv_id() -> Literal[1]:
    return 1


app.table_mapper.start_mapping()


def test_create_user(test_client, clear_db_before_and_after_test):
    user_data = {"name": "test_name", "email": "test@email.com", "password": "test_password"}
    response = test_client.post("http://127.0.0.1:5000/users/", json=user_data)
    uow = unit_of_work.UnitOfWork()
    with uow:
        user_from_repo = uow.users.get(instance_id=response.json["user_id"])
    assert response.status_code == 201
    assert response.json == {"user_id": user_from_repo.id}
    assert user_from_repo.name == user_data["name"]
    assert user_from_repo.email == user_data["email"]
    assert pass_hashing.check_password(hashed_password=user_from_repo.password, password=user_data["password"])


def test_create_user_with_integrity_error(test_client, clear_db_before_and_after_test):
    user_data = {"name": "test_name", "email": "test@email.com", "password": "test_password"}
    service_layer.create_user(user_data=user_data, validate_func=validation.validate_data_for_user_creation,
                              hash_pass_func=pass_hashing.hash_password, uow=unit_of_work.UnitOfWork())
    response = test_client.post("http://127.0.0.1:5000/users/", json=user_data)
    assert response.status_code == 409
    assert response.json == {"errors": "A user with the provided params already existsts."}


@pytest.mark.parametrize(
    "user_data,missed_param", (
            ({"name": f"test_name", "password": "test_password"}, "email"),
            ({"email": "email@test.test", "name": f"test_name"}, "password"),
            ({"email": "email@test.test", "password": "test_password"}, "name"),
    )
)
def test_create_user_where_name_or_email_or_password_missed(test_client, user_data, missed_param):
    response = test_client.post("http://127.0.0.1:5000/users/", json=user_data)
    assert response.status_code == 400
    assert response.json == {'errors': f"[{{'type': 'missing', 'loc': ('{missed_param}',), 'msg': 'Field required', "
                                       f"'input': {str(user_data)}, "
                                       f"'url': 'https://errors.pydantic.dev/2.9/v/missing'}}]"}


@pytest.mark.parametrize(
    "adv_params,extra_params", (
            (
                    {"title": "test_title", "description": "test_description"}, dict()
            ),
            (
                    {"title": "test_title", "description": "test_description"},
                    {"user_id": 5000, "id": 100, "creation_date": datetime(year=2030, month=1, day=1)}
            ),
    )
)
def test_create_adv_returns_201_and_ignores_extra_params(
        test_client, app_context, clear_db_before_and_after_test, adv_params, extra_params
):
    user_data = {"name": "test_name", "email": "test@email.test", "password": "test_pass"}
    user_id: int = service_layer.create_user(
        user_data=user_data, validate_func=validation.validate_data_for_user_creation,
        hash_pass_func=pass_hashing.hash_password, uow=unit_of_work.UnitOfWork()
    )
    uow = unit_of_work.UnitOfWork()
    with app_context:
        access_token = service_layer.jwt_auth(
            validate_func=validation.validate_login_credentials, check_pass_func=pass_hashing.check_password,
            grant_access_func=authentication.get_access_token, credentials=user_data, uow=uow
        )
    response = test_client.post(
        "http://127.0.0.1:5000/advertisements/", headers={"Authorization": f"Bearer {access_token}"},
        json={**adv_params, **extra_params}
    )
    with uow:
        adv_from_repo = uow.advs.get(instance_id=response.json["new_advertisement_id"])
    assert response.status_code == 201
    assert response.json == {"new_advertisement_id": adv_from_repo.id}
    assert adv_from_repo.title == adv_params["title"]
    assert adv_from_repo.description == adv_params["description"]
    assert adv_from_repo.user_id == user_id
    assert adv_from_repo.id != extra_params.get("id")
    assert adv_from_repo.user_id != extra_params.get("user_id")
    assert adv_from_repo.creation_date != extra_params.get("creation_date")


@pytest.mark.parametrize(
    "adv_params,type,loc,input,msg,url", (
            ({'description': 'test_description'}, 'missing', 'title', f"{{'description': 'test_description'}}",
             'Field required', 'https://errors.pydantic.dev/2.9/v/missing'),
            ({'title': 'test_title'}, 'missing', 'description', f"{{'title': 'test_title'}}", 'Field required',
             'https://errors.pydantic.dev/2.9/v/missing'),
            ({"title": True, "description": "test_description"}, "string_type", "title", "True",
             "Input should be a valid string", "https://errors.pydantic.dev/2.9/v/string_type"),
    )
)
def test_create_adv_returns_400_if_invalid_adv_params_passed(
        test_client, clear_db_before_and_after_test, app_context, adv_params, type, loc, input, msg, url
):
    user_data = {"name": "test_name", "email": "test@email.test", "password": "test_pass"}
    service_layer.create_user(
        user_data=user_data, validate_func=validation.validate_data_for_user_creation,
        hash_pass_func=pass_hashing.hash_password, uow=unit_of_work.UnitOfWork()
    )
    with app_context:
        access_token = service_layer.jwt_auth(
            validate_func=validation.validate_login_credentials, check_pass_func=pass_hashing.check_password,
            grant_access_func=authentication.get_access_token, credentials=user_data, uow=unit_of_work.UnitOfWork()
        )
    response = test_client.post(
        "http://127.0.0.1:5000/advertisements/", json=adv_params, headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 400
    assert response.json == {"errors": f"[{{'type': '{type}',"
                                       f" 'loc': ('{loc}',),"
                                       f" 'msg': '{msg}',"
                                       f" 'input': {input},"
                                       f" 'url': '{url}'}}]"}


def test_create_adv_returns_401_when_user_is_not_authenticated(test_client, clear_db_before_and_after_test):
    user_data = {"name": "test_name", "email": "test@email.test", "password": "test_pass"}
    adv_params = {"title": "test_title", "description": "test_description"}
    service_layer.create_user(user_data=user_data, validate_func=validation.validate_data_for_user_creation,
                              hash_pass_func=pass_hashing.hash_password, uow=unit_of_work.UnitOfWork())
    response = test_client.post("http://127.0.0.1:5000/advertisements/", json=adv_params,)
    assert response.status_code == 401
    assert response.json == {"msg": "Missing Authorization Header"}


def test_get_user_data_returns_200(
        clear_db_before_and_after_test, test_client, access_token, test_date, test_user_data
):
    response = test_client.get(
        "http://127.0.0.1:5000/users/1/", headers={"Authorization": f"Bearer {access_token}"}
    )
    uow = unit_of_work.UnitOfWork()
    with uow:
        user_from_repo: User = uow.users.get(instance_id=1)
    assert response.status_code == 200
    assert response.json == {"id": user_from_repo.id,
                             "name": user_from_repo.name,
                             "email": user_from_repo.email,
                             "creation_date": user_from_repo.creation_date.isoformat()}


def test_get_user_data_returns_403_when_other_user_is_authenticated(
        clear_db_before_and_after_test, test_client, access_token, test_date
):
    response = test_client.get(
        "http://127.0.0.1:5000/users/1000/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 403
    assert response.json == {"errors": "Unavailable operation."}


def test_get_adv_params(clear_db_before_and_after_test, create_adv_through_http, test_client, access_token):
    response = test_client.get(
        "http://127.0.0.1:5000/advertisements/1/", headers={"Authorization": f"Bearer {access_token}"}
    )
    uow = unit_of_work.UnitOfWork()
    with uow:
        adv_from_repo: Advertisement = uow.advs.get(instance_id=1)
    assert response.status_code == 200
    assert response.json == {"id": adv_from_repo.id,
                             "title": adv_from_repo.title,
                             "description": adv_from_repo.description,
                             "creation_date": adv_from_repo.creation_date.isoformat(),
                             "user_id": adv_from_repo.user_id}


def test_get_adv_params_returns_403_when_current_user_id_does_not_match_user_id_of_the_adv(
        clear_db_before_and_after_test, test_client, create_adv_through_http
):
    user_data_2 = {"name": "test_name_2", "email": "test_email_2",  "password": "password_2"}
    test_client.post("http://127.0.0.1:5000/users/", json=user_data_2)
    access_token: str = test_client.post("http://127.0.0.1:5000/login/", json=user_data_2).json["access_token"]
    response = test_client.get(
        "http://127.0.0.1:5000/advertisements/1/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 403
    assert response.json == {"errors": "Unavailable operation."}


def test_get_adv_params_returns_404_when_adv_is_not_found(clear_db_before_and_after_test, test_client, access_token):
    response = test_client.get(
        "http://127.0.0.1:5000/advertisements/2/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 404
    assert response.json == {"errors": "The advertisement with the provided parameters is not found."}


def test_update_user_returns_200(clear_db_before_and_after_test, test_client, access_token, test_user_data):
    new_data = {"name": "new_name"}
    response = test_client.patch(
        "http://127.0.0.1:5000/users/1/", json=new_data, headers={"Authorization": f"Bearer {access_token}"}
    )
    user_data_from_repo: dict[str, str | int] = test_client.get(
        "http://127.0.0.1:5000/users/1/", headers={"Authorization": f"Bearer {access_token}"}
    ).json
    expected = {
        **test_user_data, "id": user_data_from_repo["id"], "creation_date": user_data_from_repo["creation_date"]
    }
    assert response.status_code == 200
    assert response.json == {"modified_data": {"id": expected["id"],
                                               "name": new_data["name"],
                                               "email": expected["email"],
                                               "creation_date": expected["creation_date"]}}


def test_update_user_returns_403_when_user_has_no_authority_to_update(
        clear_db_before_and_after_test, create_user_through_http, test_client, access_token
):
    new_data = {"name": "new_name"}
    response = test_client.patch("http://127.0.0.1:5000/users/10/", json=new_data,
                                 headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 403
    assert response.json == {"errors": "Unavailable operation."}


def test_get_related_advs_returns_200(
        clear_db_before_and_after_test, test_client, access_token, create_adv_through_http, test_date, test_adv_params
):
    response = test_client.get(f"http://127.0.0.1:5000/users/1/advertisements",
                               headers={"Authorization": f"Bearer {access_token}"})
    adv_params_from_repo: dict[str, str | int] = test_client.get(
        "http://127.0.0.1:5000/advertisements/1/", headers={"Authorization": f"Bearer {access_token}"}
    ).json
    expected = {
        **test_adv_params, "id": adv_params_from_repo["id"], "creation_date": adv_params_from_repo["creation_date"],
        "user_id": adv_params_from_repo["user_id"]
    }
    assert response.status_code == 200
    assert response.json == {"items": [{"id": expected["id"],
                                        "title": expected["title"],
                                        "description": expected["description"],
                                        "creation_date": expected["creation_date"],
                                        "user_id": expected["user_id"]}],
                             "page": 1,
                             "per_page": 10,
                             "total": 1,
                             "total_pages": 1}


def test_get_related_advs_returns_200_when_page_value_exceeds_total_page_number(
        clear_db_before_and_after_test, test_client, access_token, create_adv_through_http, test_adv_params
):
    page = 100
    response = test_client.get(
        f"http://127.0.0.1:5000/users/1/advertisements?page={page}", headers={"Authorization": f"Bearer {access_token}"}
    )
    adv_params_from_repo: dict[str, str | int] = test_client.get(
        "http://127.0.0.1:5000/advertisements/1/", headers={"Authorization": f"Bearer {access_token}"}
    ).json
    expected = {
        **test_adv_params, "id": adv_params_from_repo["id"], "creation_date": adv_params_from_repo["creation_date"],
        "user_id": adv_params_from_repo["user_id"]
    }
    assert response.status_code == 200
    assert response.json == {"items": [{"id": expected["id"],
                                        "title": expected["title"],
                                        "description": expected["description"],
                                        "creation_date": expected["creation_date"],
                                        "user_id": expected["user_id"]}],
                             "page": 1,
                             "per_page": 10,
                             "total": 1,
                             "total_pages": 1}


def test_get_related_advs_returns_200_when_page_and_per_page_params_are_not_passed(
        clear_db_before_and_after_test, test_client, access_token, create_adv_through_http, test_adv_params
):
    response = test_client.get(
        "http://127.0.0.1:5000/users/1/advertisements", headers={"Authorization": f"Bearer {access_token}"}
    )
    adv_params_from_repo: dict[str, str | int] = test_client.get(
        "http://127.0.0.1:5000/advertisements/1/", headers={"Authorization": f"Bearer {access_token}"}
    ).json
    expected = {
        **test_adv_params, "id": adv_params_from_repo["id"], "creation_date": adv_params_from_repo["creation_date"],
        "user_id": adv_params_from_repo["user_id"]
    }
    assert response.status_code == 200
    assert response.json == {"items": [{"id": expected["id"],
                                        "title": expected["title"],
                                        "description": expected["description"],
                                        "creation_date": expected["creation_date"],
                                        "user_id": expected["user_id"]}],
                             "page": 1,
                             "per_page": 10,
                             "total": 1,
                             "total_pages": 1}


def test_get_related_advs_returns_200_when_incorrect_page_and_per_page_params_passed(
        clear_db_before_and_after_test, test_client, access_token, create_adv_through_http, test_adv_params
):
    response = test_client.get("http://127.0.0.1:5000/users/1/advertisements?per_page=error&page=error",
                               headers={"Authorization": f"Bearer {access_token}"})
    adv_params_from_repo: dict[str, str | int] = test_client.get(
        "http://127.0.0.1:5000/advertisements/1/", headers={"Authorization": f"Bearer {access_token}"}
    ).json
    expected = {
        **test_adv_params, "id": adv_params_from_repo["id"], "creation_date": adv_params_from_repo["creation_date"],
        "user_id": adv_params_from_repo["user_id"]
    }
    assert response.status_code == 200
    assert response.json == {"items": [{"id": expected["id"],
                                        "title": expected["title"],
                                        "description": expected["description"],
                                        "creation_date": expected["creation_date"],
                                        "user_id": expected["user_id"]}],
                             "page": 1,
                             "per_page": 10,
                             "total": 1,
                             "total_pages": 1}


def test_search_advs_by_text_returns_200(
        clear_db_before_and_after_test, create_adv_through_http, test_client, test_adv_params
):
    response = test_client.get("http://127.0.0.1:5000/advertisements?column_value=test")
    assert response.status_code == 200
    assert response.json == {"items": [{test_adv_params["title"]: test_adv_params["description"]}],
                             "page": 1,
                             "per_page": 10,
                             "total": 1,
                             "total_pages": 1}


def test_search_advs_by_text_returns_200_when_text_is_missing(
        clear_db_before_and_after_test, create_adv_through_http, test_client, test_adv_params
):
    response = test_client.get("http://127.0.0.1:5000/advertisements")
    assert response.status_code == 200
    assert response.json == {"items": [],
                             "page": 1,
                             "per_page": 10,
                             "total": 0,
                             "total_pages": 0}


def test_search_advs_by_text_returns_200_when_text_is_not_found(
        clear_db_before_and_after_test, create_adv_through_http, test_client, test_adv_params
):
    response = test_client .get("http://127.0.0.1:5000/advertisements?column_value=no_text")
    assert response.status_code == 200
    assert response.json == {"items": [],
                             "page": 1,
                             "per_page": 10,
                             "total": 0,
                             "total_pages": 0}


def test_search_advs_by_text_returns_400_when_invalid_params_passed(
        clear_db_before_and_after_test, create_adv_through_http, test_client, test_adv_params
):
    response = test_client .get("http://127.0.0.1:5000/advertisements?column=invalid_param")
    assert response.status_code == 400
    assert set(response.json["errors"]) == set(
        "{"
            "'params_passed': {'"
                    "'model_class': <class 'app.models.Advertisement'>, "
                    "'filter_type': <FilterTypes.SEARCH_TEXT: 'search_text'>, "
                    "'comparison': <Comparison.IS: 'is'>, "
                    "'column': 'invalid_param'"
            "}, "
             "'missing_params': ['column_value'], "
             "'invalid_params': {"
                    "'column': 'For model class \"Advertisement\" text search is available in the '"
                    "following columns: [\\'title\\', \\'description\\'].'"
        "}"
    )


def test_update_adv_returns_200(
        clear_db_before_and_after_test, test_client, app_context, test_user_data, test_adv_params,
        create_user_through_http, create_adv_through_http, test_adv_id, access_token
):
    new_adv_params = {"title": "new_title", "description": "new_description"}
    response = test_client.patch(
        f"http://127.0.0.1:5000/advertisements/{test_adv_id}/", headers={"Authorization": f"Bearer {access_token}"},
        json=new_adv_params
    )
    expected: dict[str, str | int] = test_client.get(f"http://127.0.0.1:5000/advertisements/{test_adv_id}/",
                                                     headers={"Authorization": f"Bearer {access_token}"}).json
    assert response.status_code == 200
    assert response.json["updated_adv_params"] == expected
    assert response.json["updated_adv_params"]["title"] == new_adv_params["title"]
    assert response.json["updated_adv_params"]["description"] == new_adv_params["description"]


def test_update_adv_returns_404_when_adv_is_not_found(
        clear_db_before_and_after_test, test_client, access_token, test_adv_id
):
    new_adv_params = {"title": "new_title", "description": "new_description"}
    response = test_client.patch(
        f"http://127.0.0.1:5000/advertisements/{test_adv_id}/", headers={"Authorization": f"Bearer {access_token}"},
        json=new_adv_params
    )
    assert response.status_code == 404
    assert response.json == {"errors": "The advertisement with the provided parameters is not found."}


@pytest.mark.parametrize(
    "new_adv_params,type,loc,input,msg,url", (
            ({"title": False, "description": "new_description"}, 'string_type', 'title', f"{False}",
             'Input should be a valid string', 'https://errors.pydantic.dev/2.9/v/string_type'),
            ({"description": 1}, 'string_type', 'description', f"{1}", 'Input should be a valid string',
             'https://errors.pydantic.dev/2.9/v/string_type'),
    )
)
def test_update_adv_returns_400_when_invalid_new_adv_params_passed(
        clear_db_before_and_after_test, test_client, create_adv_through_http, access_token, test_adv_id, new_adv_params,
        type, loc, input, msg, url
):
    response = test_client.patch(
        f"http://127.0.0.1:5000/advertisements/{test_adv_id}/", headers={"Authorization": f"Bearer {access_token}"},
        json=new_adv_params
    )
    assert response.status_code == 400
    assert response.json == {
        "errors": f"[{{'type': '{type}', 'loc': ('{loc}',), 'msg': '{msg}', 'input': {input}, 'url': '{url}'}}]"
    }


def test_update_adv_returns_403_when_current_user_check_fails(
        clear_db_before_and_after_test, test_client, create_adv_through_http, access_token, test_adv_id
):
    new_adv_params = {"title": "new_title"}
    other_user_data = {"name": "other_name", "email": "other_email", "password": "other_pass"}
    test_client.post("http://127.0.0.1:5000/users/", json=other_user_data)
    other_user_access_token = \
        test_client.post("http://127.0.0.1:5000/login/", json=other_user_data).json.get("access_token")
    response = test_client.patch(
        f"http://127.0.0.1:5000/advertisements/{test_adv_id}/", json=new_adv_params,
        headers={"Authorization": f"Bearer {other_user_access_token}"}
    )
    assert response.status_code == 403
    assert response.json == {"errors": "Unavailable operation."}


def test_update_adv_returns_401_when_user_is_not_authenticated(
        clear_db_before_and_after_test, test_client, create_adv_through_http, test_adv_id
):
    new_adv_params = {"title": "new_title"}
    response = test_client.patch(f"http://127.0.0.1:5000/advertisements/{test_adv_id}/", json=new_adv_params)
    assert response.status_code == 401
    assert response.json == {'msg': 'Missing Authorization Header'}


def test_delete_user_returns_200(clear_db_before_and_after_test, test_client, access_token, create_adv_through_http):
    response = test_client.delete("http://127.0.0.1:5000/users/1/", headers={"Authorization": f"Bearer {access_token}"})
    response_for_deleted_user = test_client.get(
        "http://127.0.0.1:5000/users/1/", headers={"Authorization": f"Bearer {access_token}"}
    )
    response_for_related_adv = test_client.get(
        "http://127.0.0.1:5000/users/1/advertisements", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response_for_deleted_user.status_code == response_for_related_adv.status_code == 404
    assert response_for_deleted_user.json == {"errors": "The user with the provided parameters is not found."}
    assert response_for_related_adv.json == {"errors": "The related advertisements are not found."}


def test_delete_user_returns_status_403_when_current_user_check_fails(test_client, access_token):
    response = test_client.delete("http://127.0.0.1:5000/users/1000/",
                                  headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 403
    assert response.json == {"errors": "Unavailable operation."}


def test_delete_user_returns_status_401_when_user_is_not_authenticated(test_client, access_token):
    response = test_client.delete("http://127.0.0.1:5000/users/1/")
    assert response.status_code == 401
    assert response.json == {"msg": "Missing Authorization Header"}


def test_delete_adv_returns_200(
        clear_db_before_and_after_test, access_token, create_adv_through_http, test_client, test_adv_params
):
    get_request_before_deletion = test_client.get(
        f"http://127.0.0.1:5000/advertisements/1/", headers={"Authorization": f"Bearer {access_token}"}
    )
    response = test_client.delete(
        f"http://127.0.0.1:5000/advertisements/1/", headers={"Authorization": f"Bearer {access_token}"}
    )
    get_request_after_deletion = test_client.get(
        f"http://127.0.0.1:5000/advertisements/1/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json == {
        "deleted_advertisement_params": {"id": get_request_before_deletion.json["id"],
                                         "title": get_request_before_deletion.json["title"],
                                         "description": get_request_before_deletion.json["description"],
                                         "creation_date": get_request_before_deletion.json["creation_date"],
                                         "user_id": get_request_before_deletion.json["user_id"]}
    }
    assert get_request_after_deletion.status_code == 404
    assert get_request_after_deletion.json == {"errors": "The advertisement with the provided parameters is not found."}


def test_delete_adv_returns_403_when_user_has_no_authority(
        clear_db_before_and_after_test, test_client, access_token, create_adv_through_http
):
    # Creation of a "wrong" user and access token for him
    wrong_user_data = {"name": "wrong_name", "email": "wrong_email", "password": "wrong_pass"}
    test_client.post("http://127.0.0.1:5000/users/", json=wrong_user_data)
    wrong_user_access_token: str = test_client.post("http://127.0.0.1:5000/login/", json=wrong_user_data).json[
        "access_token"
    ]
    # Delete request with "wrong_user_access_token" (that what we test here)
    response = test_client.delete("http://127.0.0.1:5000/advertisements/1/",
                                  headers={"Authorization": f"Bearer {wrong_user_access_token}"})
    assert response.status_code == 403
    assert response.json == {"errors": "Unavailable operation."}


def test_delete_adv_returns_404_when_adv_is_not_found(clear_db_before_and_after_test, access_token, test_client):
    response = test_client.delete(
        f"http://127.0.0.1:5000/advertisements/1/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 404
    assert response.json == {"errors": "The advertisement with the provided parameters is not found."}


def test_login_returns_200(clear_db_before_and_after_test, test_client, create_user_through_http, test_user_data):
    response = test_client.post("http://127.0.0.1:5000/login/", json=test_user_data)
    assert response.status_code == 200
    assert response.json["access_token"]
    assert type(response.json["access_token"]) == str
    assert len(response.json["access_token"]) >= 32


def test_login_returns_401_when_user_with_the_provided_credentials_is_not_found(test_client):
    wrong_credentials = {"email": "does_not@exist.com", "password": "does_not_exist_pass"}
    response = test_client.post("http://127.0.0.1:5000/login/", json=wrong_credentials)
    assert response.status_code == 401
    assert response.json == {"errors": "Invalid credentials."}


@pytest.mark.parametrize(
    "input_data, missed_field", (({"password": "password"}, "email"), ({"email": "test_2@email.com"}, "password"))
)
def test_login_returns_400_when_incomplete_credentials_passed(test_client, input_data, missed_field):
    response = test_client.post("http://127.0.0.1:5000/login/", json=input_data)
    assert response.status_code == 400
    assert response.json == {
        "errors": f"[{{'type': 'missing', 'loc': ('{missed_field}',), 'msg': 'Field required', 'input': {input_data}, "
                  f"'url': 'https://errors.pydantic.dev/2.9/v/missing'}}]"
    }
