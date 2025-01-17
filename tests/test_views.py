import pytest
import sqlalchemy

from datetime import datetime

from app import models, pass_hashing, authentication
from app.error_handlers import HttpError


@pytest.fixture(scope="function", autouse=True)
def register_urls():
    from app import views


@pytest.mark.run(order=1)
def test_create_user(test_client, session_maker, engine):
    user_data = {"name": "test_name", "email": "test@email.com", "password": "test_password"}
    response = test_client.post("http://127.0.0.1:5000/users/", json=user_data)
    session = session_maker
    with session() as sess:
        data_from_db = sess.execute(sqlalchemy.text('SELECT * from "user"')).first()
        sess.execute(sqlalchemy.text('DELETE from "user"'))
        sess.commit()
    assert response.status_code == 201
    assert response.json == {"user id": data_from_db[0]}
    assert data_from_db[1] == user_data["name"]
    assert data_from_db[2] == user_data["email"]
    assert pass_hashing.check_password(hashed_password=data_from_db[3], password=user_data["password"])


def test_create_user_with_integrity_error(test_client, session_maker, engine, create_test_users_and_advs):
    user_data = {"name": f"test_filter_1000", "email": f"test_filter_1000@email.com", "password": "password"}
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
def test_create_user_where_name_or_email_or_password_missed(
        test_client, session_maker, engine, user_data, missed_param
):
    response = test_client.post("http://127.0.0.1:5000/users/", json=user_data)
    assert response.status_code == 400
    assert response.json == {'errors': f"[{{'type': 'missing', 'loc': ('{missed_param}',), 'msg': 'Field required', "
                                       f"'input': {str(user_data)}, "
                                       f"'url': 'https://errors.pydantic.dev/2.9/v/missing'}}]"}


@pytest.mark.run(order=2)
@pytest.mark.parametrize(
    "adv_params, adv_id, user",
    (
            ({"title": "test_title_1", "description": "test_description_1"}, 1, "user_1"),
            ({"title": "test_title_2", "description": "test_description_2"}, 2, "user_1"),
            ({"title": "test_title_3", "description": "test_description_3"}, 3, "user_2"),
            ({"title": "test_title_4", "description": "test_description_4"}, 4, "user_2"),
    )
)
def test_create_adv(test_client, session_maker, engine, adv_params, user, adv_id, access_token, app_context):
    with app_context:
        response = test_client.post("http://127.0.0.1:5000/advertisements/",
                                    json=adv_params,
                                    headers={"Authorization": f"Bearer {access_token[user]}"})
        authenticated_user_id = authentication.get_authenticated_user_identity()
    session = session_maker
    with session() as sess:
        sql_statement = sqlalchemy.text('SELECT * from "adv" WHERE id = :id')
        data_from_db = sess.execute(sql_statement, dict(id=adv_id)).first()
    assert response.status_code == 201
    assert response.json == {"advertisement id": adv_id}
    assert response.json["advertisement id"] == data_from_db[0]
    assert data_from_db[1] == adv_params["title"]
    assert data_from_db[2] == adv_params["description"]
    assert data_from_db[4] == authenticated_user_id


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
def test_get_adv_params(test_client, session_maker, access_token):
    response = test_client.get("http://127.0.0.1:5000/advertisements/1/",
                               headers={"Authorization": f"Bearer {access_token['user_1']}"})
    session = session_maker
    with session() as sess:
        data_from_db = sess.execute(sqlalchemy.text('SELECT * FROM "adv" WHERE id = 1')).first()
    assert response.status_code == 200
    assert response.json == {"id": data_from_db[0],
                             "title": data_from_db[1],
                             "description": data_from_db[2],
                             "creation_date": data_from_db[3].isoformat(),
                             "user_id": data_from_db[4]}


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
def test_update_user_with_incorrect_input_data(test_client, session_maker, access_token):
    new_data = {"name": "new_name"}
    response = test_client.patch("http://127.0.0.1:5000/users/10/",
                                 json=new_data,
                                 headers={"Authorization": f"Bearer {access_token['user_1000']}"})
    assert response.status_code == 403
    assert response.json == {"errors": "Forbidden action."}


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
def test_search_advs_by_text(test_client, create_test_users_and_advs):
    response = test_client \
        .get("http://127.0.0.1:5000/advertisements?filter_type=search_text&column=description&column_value=01")
    assert response.status_code == 200
    assert response.json == {"items": [{"test_filter_1001": "test_filter_1001"}],
                             "page": 1,
                             "per_page": 10,
                             "total": 1,
                             "total_pages": 1}


def test_search_advs_by_text_where_text_is_missing(test_client, create_test_users_and_advs):
    response = test_client \
        .get("http://127.0.0.1:5000/advertisements?filter_type=search_text&column=description")
    assert response.status_code == 200
    assert response.json == {"items": [],
                             "page": 1,
                             "per_page": 10,
                             "total": 0,
                             "total_pages": 0}


def test_search_advs_by_text_where_text_is_not_found(test_client, create_test_users_and_advs):
    response = test_client \
        .get("http://127.0.0.1:5000/advertisements?filter_type=search_text&column=description&column_value=no_text")
    assert response.status_code == 200
    assert response.json == {"items": [],
                             "page": 1,
                             "per_page": 10,
                             "total": 0,
                             "total_pages": 0}


@pytest.mark.run(order=20)
def test_update_adv(test_client, session_maker, access_token):
    new_data = {"title": "new_title"}
    response = test_client.patch("http://127.0.0.1:5000/advertisements/1000/",
                                 json=new_data,
                                 headers={"Authorization": f"Bearer {access_token['user_1000']}"})
    session = session_maker
    with session() as sess:
        data_from_db = sess.execute(sqlalchemy.text('SELECT * FROM "adv" WHERE id = 1000')).first()
    assert response.status_code == 200
    assert response.json == {"modified advertisement params": {"id": data_from_db[0],
                                                               "title": data_from_db[1],
                                                               "description": data_from_db[2],
                                                               "creation_date": data_from_db[3].isoformat(),
                                                               "user_id": data_from_db[4]}}


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
