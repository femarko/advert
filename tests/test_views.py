from typing import Literal

import pytest
import sqlalchemy

from datetime import datetime

from flask_jwt_extended import verify_jwt_in_request

import app.service_layer
from app import models, pass_hashing, authentication, validation, service_layer, unit_of_work, errors, services
from app.error_handlers import HttpError
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


@pytest.mark.run(order=1)
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
    assert response.json == {"errors": "A user with the provided credentials already existsts."}


@pytest.mark.parametrize(
    "user_data,missed_param", (
            ({"name": f"test_name", "password": "test_password"}, "email"),
            ({"email": "email@test.test", "name": f"test_name"}, "password"),
            ({"email": "email@test.test", "password": "test_password"}, "name"),
    )
)
def test_create_user_where_name_or_email_or_password_missed(test_client, engine, user_data, missed_param):
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
def test_create_adv_returns_400_if_invalid_adv_params_passed(test_client, clear_db_before_and_after_test, app_context,
                                                             adv_params, type, loc, input, msg, url):
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


@pytest.mark.run(order=12)
def test_get_user_data(test_client, access_token, test_date):
    response = test_client.get(
        "http://127.0.0.1:5000/users/1000/", headers={"Authorization": f"Bearer {access_token['user_1000']}"}
    )
    assert response.status_code == 200
    assert response.json == {"id": 1000,
                             "name": f"test_filter_1000",
                             "email": "test_filter_1000@email.com",
                             "creation_date": test_date.isoformat()}


def test_get_user_data_by_other_user(test_client, access_token, test_date):
    response = test_client.get(
        "http://127.0.0.1:5000/users/1000/", headers={"Authorization": f"Bearer {access_token['user_1001']}"}
    )
    assert response.status_code == 403
    assert response.json == {"errors": "Unavailable operation."}


@pytest.mark.run(order=13)
def test_get_adv_params(test_client, clear_db_before_and_after_test, app_context, fake_get_auth_user_id_func):
    user_data = {"name": "test_name", "email": "test@email.test", "password": "test_pass"}
    user_id: int = service_layer.create_user(
        user_data=user_data, validate_func=validation.validate_data_for_user_creation,
        hash_pass_func=pass_hashing.hash_password, uow=unit_of_work.UnitOfWork()
    )
    adv_params = {"title": "test_title", "description": "test_description", "user_id": user_id}
    adv = services.create_adv(**adv_params)
    uow = unit_of_work.UnitOfWork()
    with uow:
        uow.advs.add(instance=adv)
        uow.commit()
        with app_context:
            access_token = service_layer.jwt_auth(
                validate_func=validation.validate_login_credentials, check_pass_func=pass_hashing.check_password,
                grant_access_func=authentication.get_access_token, credentials=user_data, uow=uow
            )
        expected = uow.advs.get(instance_id=1)
    response = test_client.get(
        "http://127.0.0.1:5000/advertisements/1/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200
    assert response.json == {"id": expected.id,
                             "title": expected.title,
                             "description": expected.description,
                             "creation_date": expected.creation_date.isoformat(),
                             "user_id": expected.user_id}


def test_get_adv_params_returns_403_when_current_user_id_does_not_match_user_id_of_the_adv(
        clear_db_before_and_after_test, app_context, test_client
):
    password_1 = "test_pass_1"
    password_2 = "test_pass_2"
    user_data_1 = {"name": "test_name_1", "email": "test_email_1", "password": pass_hashing.hash_password(password_1)}
    user_data_2 = {"name": "test_name_2", "email": "test_email_2", "password": pass_hashing.hash_password(password_2)}
    adv_params = {"user_id": 2, "title": "test_title", "description": "test_description"}
    user_1: User = services.create_user(**user_data_1)
    user_2: User = services.create_user(**user_data_2)
    adv: Advertisement = services.create_adv(**adv_params)
    uow = unit_of_work.UnitOfWork()
    with uow:
        uow.users.add(instance=user_1)
        uow.users.add(instance=user_2)
        uow.advs.add(instance=adv)
        uow.commit()
    with app_context:
        access_token = service_layer.jwt_auth(
            validate_func=validation.validate_login_credentials, check_pass_func=pass_hashing.check_password,
            grant_access_func=authentication.get_access_token,
            credentials={"email": user_data_1["email"], "password": password_1}, uow=uow
        )
    response = test_client.get(
        "http://127.0.0.1:5000/advertisements/1/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 403
    assert response.json == {"errors": "Unavailable operation."}


def test_get_adv_params_returns_404_when_adv_is_not_found(clear_db_before_and_after_test, test_client, app_context):
    password = "test_pass_1"
    user_data = {"name": "test_name_1", "email": "test_email_1", "password": pass_hashing.hash_password(password)}
    user: User = services.create_user(**user_data)
    uow = unit_of_work.UnitOfWork()
    with uow:
        uow.users.add(instance=user)
        uow.commit()
    with app_context:
        access_token = service_layer.jwt_auth(
            validate_func=validation.validate_login_credentials, check_pass_func=pass_hashing.check_password,
            grant_access_func=authentication.get_access_token,
            credentials={"email": user_data["email"], "password": password}, uow=uow
        )
    response = test_client.get(
        "http://127.0.0.1:5000/advertisements/1/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 404
    assert response.json == {"errors": "The advertisement with the provided parameters is not found."}


@pytest.mark.run(order=14)
def test_update_user_with_correct_input_data(test_client, session_maker, access_token):
    new_data = {"name": "new_name"}
    response = test_client.patch("http://127.0.0.1:5000/users/1000/",
                                 json=new_data,
                                 headers={"Authorization": f"Bearer {access_token['user_1000']}"})
    session = session_maker
    with session() as sess:
        data_from_db = \
            sess.execute(sqlalchemy.text('SELECT id, name, email, creation_date FROM "user" WHERE id = 1000')).first()
    assert response.status_code == 200
    assert response.json == {"modified_data": {"id": data_from_db[0],
                                               "name": data_from_db[1],
                                               "email": data_from_db[2],
                                               "creation_date": data_from_db[3].isoformat()}}


@pytest.mark.run(order=15)
def test_update_user_with_incorrect_input_data(test_client, access_token):
    new_data = {"name": "new_name"}
    response = test_client.patch("http://127.0.0.1:5000/users/10/", json=new_data,
                                 headers={"Authorization": f"Bearer {access_token['user_1000']}"})
    assert response.status_code == 403
    assert response.json == {"errors": "Unavailable operation."}


def test_get_related_advs_represented_in_one_page(test_client, session_maker, access_token, test_date):
    response = test_client.get(f"http://127.0.0.1:5000/users/1000/advertisements?per_page=2&page=1",
                               headers={"Authorization": f"Bearer {access_token['user_1000']}"})
    assert response.status_code == 200
    assert response.json == {"items": [{"id": 1000,
                                        "title": f"test_filter_1000",
                                        "description": "test_filter_1000",
                                        "creation_date": test_date.isoformat(),
                                        "user_id": 1000},
                                       {"id": 1003,
                                        "title": f"test_filter_1003",
                                        "description": "test_filter_1003",
                                        "creation_date": test_date.isoformat(),
                                        "user_id": 1000}],
                             "page": 1,
                             "per_page": 2,
                             "total": 2,
                             "total_pages": 1}


@pytest.mark.parametrize("page,adv_id", ((1, 1000), (2, 1003)))
def test_get_related_advs_represented_in_two_pages(
        test_client, session_maker, access_token, test_date, page, adv_id
):
    response = test_client.get(f"http://127.0.0.1:5000/users/1000/advertisements?per_page=1&page={page}",
                               headers={"Authorization": f"Bearer {access_token['user_1000']}"})
    assert response.status_code == 200
    assert response.json == {"items": [{"id": adv_id,
                                        "title": f"test_filter_{adv_id}",
                                        "description": f"test_filter_{adv_id}",
                                        "creation_date": test_date.isoformat(),
                                        "user_id": 1000}],
                             "page": page,
                             "per_page": 1,
                             "total": 2,
                             "total_pages": 2}


@pytest.mark.run(order=18)
def test_get_related_advs_where_page_number_is_out_of_range(test_client, session_maker, access_token):
    response = test_client.get("http://127.0.0.1:5000/users/1000/advertisements?page=100",
                               headers={"Authorization": f"Bearer {access_token['user_1000']}"})
    assert response.status_code == 200
    assert response.json == {"items": [],
                             "page": 100,
                             "per_page": 10,
                             "total": 2,
                             "total_pages": 1}


def test_get_related_advs_where_page_and_per_page_params_are_not_passed(
        test_client, session_maker, access_token, test_date
):
    response = test_client.get("http://127.0.0.1:5000/users/1000/advertisements",
                               headers={"Authorization": f"Bearer {access_token['user_1000']}"})
    assert response.status_code == 200
    assert response.json == {"items": [{"id": 1000,
                                        "title": f"test_filter_1000",
                                        "description": "test_filter_1000",
                                        "creation_date": test_date.isoformat(),
                                        "user_id": 1000},
                                       {"id": 1003,
                                        "title": f"test_filter_1003",
                                        "description": "test_filter_1003",
                                        "creation_date": test_date.isoformat(),
                                        "user_id": 1000}],
                             "page": 1,
                             "per_page": 10,
                             "total": 2,
                             "total_pages": 1}


def test_get_related_advs_with_incorrect_page_and_per_page_params(
        test_client, session_maker, access_token, test_date
):
    response = test_client.get("http://127.0.0.1:5000/users/1000/advertisements?per_page=error&page=error",
                               headers={"Authorization": f"Bearer {access_token['user_1000']}"})
    assert response.status_code == 200
    assert response.json == {"items": [{"id": 1000,
                                        "title": f"test_filter_1000",
                                        "description": "test_filter_1000",
                                        "creation_date": test_date.isoformat(),
                                        "user_id": 1000},
                                       {"id": 1003,
                                        "title": f"test_filter_1003",
                                        "description": "test_filter_1003",
                                        "creation_date": test_date.isoformat(),
                                        "user_id": 1000}],
                             "page": 1,
                             "per_page": 10,
                             "total": 2,
                             "total_pages": 1}


@pytest.mark.run(order=19)
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
    assert response.json == {'errors': '["For filter_type=<FilterTypes.SEARCH_TEXT: \'search_text\'> '
                                       "the folowing columns are available: {for <class 'app.models.User'>: "
                                       "[name, email], for <class 'app.models.Advertisement'>: [title, "
                                       'description]}", "\'invalid_param\' is invalid value for '
                                       "'column'. Valid values: ['id', 'title', 'description', "
                                       '\'creation_date\', \'user_id\']."]'}



@pytest.mark.run(order=20)
def test_update_adv_returns_200(
        clear_db_before_and_after_test, test_client, app_context, test_user_data, test_adv_params,
        create_user_through_http, create_adv_through_http, test_adv_id, access_token
):
    new_adv_params = {"title": "new_title", "description": "new_description"}
    access_token = access_token
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


def test_update_adv_returns_401_when_user_is_unauthorized(
        clear_db_before_and_after_test, test_client, create_adv_through_http, test_adv_id
):
    new_adv_params = {"title": "new_title"}
    response = test_client.patch(f"http://127.0.0.1:5000/advertisements/{test_adv_id}/", json=new_adv_params)
    assert response.status_code == 401
    assert response.json == {'msg': 'Missing Authorization Header'}



@pytest.mark.run(order=21)
def test_get_related_user(test_client, session_maker, access_token):
    response = test_client.get("http://127.0.0.1:5000/advertisements/1/user",
                               headers={"Authorization": f"Bearer {access_token['user_1']}"})
    session = session_maker
    with session() as sess:
        data_from_db = \
            sess.execute(sqlalchemy.text('SELECT id, name, email, creation_date FROM "user" WHERE id = 1')).first()
    assert response.status_code == 200
    assert response.json == {"id": data_from_db[0],
                             "name": data_from_db[1],
                             "email": data_from_db[2],
                             "creation_date": data_from_db[3].isoformat()}


@pytest.mark.run(order=22)
def test_delete_adv_with_wrong_authorized_user(test_client, session_maker, access_token):
    response = test_client.delete("http://127.0.0.1:5000/advertisements/2/",
                                  headers={"Authorization": f"Bearer {access_token['user_2']}"})
    session = session_maker
    with session() as sess:
        data_from_db = sess.execute(sqlalchemy.text('SELECT * FROM "adv" WHERE id = 2')).first()
    assert response.status_code == 403
    assert response.json == {"error": "Forbidden."}
    assert data_from_db is not None


@pytest.mark.run(order=23)
def test_delete_user(test_client, session_maker, access_token):
    response = test_client.delete("http://127.0.0.1:5000/users/1000/",
                                  headers={"Authorization": f"Bearer {access_token['user_1000']}"})
    session = session_maker
    with session() as sess:
        user_from_db = sess.execute(sqlalchemy.text('SELECT * FROM "user" WHERE id = 1000')).first()
        related_adv_from_db = sess.execute(sqlalchemy.text('SELECT * FROM "adv" WHERE user_id = 1000')).first()
    assert response.status_code == 200
    assert user_from_db is None
    assert related_adv_from_db is None


def test_delete_user_returns_status_403_when_current_user_check_fails(test_client, session_maker, access_token):
    response = test_client.delete("http://127.0.0.1:5000/users/1000/",
                                  headers={"Authorization": f"Bearer {access_token['user_1001']}"})
    assert response.status_code == 403
    assert response.json == {"errors": "Unavailable operation."}


def test_delete_user_returns_status_401_when_user_is_not_authenticated(test_client, session_maker, access_token):
    response = test_client.delete("http://127.0.0.1:5000/users/1000/")
    assert response.status_code == 401
    assert response.json == {"msg": "Missing Authorization Header"}


@pytest.mark.run(order=24)
def test_delete_adv(test_client, session_maker, access_token):
    session = session_maker
    with session() as sess:
        data_from_db_before_request = sess.execute(sqlalchemy.text('SELECT * FROM "adv" WHERE id = 1000')).first()
    response = test_client.delete("http://127.0.0.1:5000/advertisements/1000/",
                                  headers={"Authorization": f"Bearer {access_token['user_1000']}"})
    session = session_maker
    with session() as sess:
        data_from_db_after_request = sess.execute(sqlalchemy.text('SELECT * FROM "adv" WHERE id = 1000')).first()
    assert response.status_code == 200
    assert response.json == {"deleted advertisement params": {"id": data_from_db_before_request[0],
                                                              "title": data_from_db_before_request[1],
                                                              "description": data_from_db_before_request[2],
                                                              "creation_date":
                                                                  data_from_db_before_request[3].isoformat(),
                                                              "user_id": data_from_db_before_request[4]}}
    assert data_from_db_after_request is None


@pytest.mark.run(order=25)
def test_login_with_correct_credentials(test_client, app_context, create_test_users_and_advs):
    with app_context:
        response = test_client.post("http://127.0.0.1:5000/login/",
                                    json={"email": "test_filter_1000@email.com", "password": "test_filter_1000_pass"})
    assert response.status_code == 200
    assert response.json["access_token"]
    assert type(response.json["access_token"]) == str
    assert len(response.json["access_token"]) >= 32


@pytest.mark.run(order=26)
@pytest.mark.parametrize(
    "input_data",
    (
            {"email": "incorrect@email.com", "password": "incorrect_password"},
            {"email": "test_2@email.com", "password": "incorrect_password"},
            {"email": "incorrect@email.com", "password": "incorrect_password"}
    )
)
def test_login_with_incorrect_credentials(test_client, app_context, input_data):
    response = test_client.post("http://127.0.0.1:5000/login/", json=input_data)
    assert response.status_code == 401
    assert response.json == {"errors": "Invalid credentials."}


@pytest.mark.run(order=27)
@pytest.mark.parametrize(
    "input_data, missed_field",
    (
            ({"password": "password"}, "email"),
            ({"email": "test_2@email.com"}, "password")
    )
)
def test_login_with_incomplete_credentials(test_client, input_data, missed_field):
    response = test_client.post("http://127.0.0.1:5000/login/", json=input_data)
    assert response.status_code == 400
    assert response.json == {
        "errors": f"[{{'type': 'missing', 'loc': ('{missed_field}',), 'msg': 'Field required', 'input': {input_data}, "
                  f"'url': 'https://errors.pydantic.dev/2.9/v/missing'}}]"
    }
