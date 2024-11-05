import pytest
import sqlalchemy
from flask import url_for

from app import models, pass_hashing


@pytest.fixture(scope="function", autouse=True)
def register_urls():
    from app import views


@pytest.mark.parametrize(
    "user_data, user_id",
    (
            ({"name": "test_name_1", "email": "test_1@email.com", "password": "test_password_1"}, 1),
            ({"name": "test_name_2", "email": "test_2@email.com", "password": "test_password_2"}, 2)
    )
)
def test_create_user(test_client, session_maker, engine, user_data, user_id, drop_all_create_all):
    response = test_client.post("http://127.0.0.1:5000/users/", json=user_data)
    session = session_maker
    with session() as sess:
        sql_statement = sqlalchemy.text('SELECT * from "user" WHERE id = :id')
        data_from_db = sess.execute(sql_statement, dict(id=user_id)).first()
    assert response.status_code == 201
    assert response.json == {"user id": user_id}
    assert response.json["user id"] == data_from_db[0]
    assert data_from_db[1] == user_data["name"]
    assert data_from_db[2] == user_data["email"]
    assert pass_hashing.check_password(data_from_db[3], user_data["password"])


@pytest.mark.parametrize(
    "adv_params, adv_id",
    (
            ({"title": "test_title_1", "description": "test_description_1", "user_id": 1}, 1),
            ({"title": "test_title_2", "description": "test_description_2", "user_id": 2}, 2)
    )
)
def test_create_adv(test_client, session_maker, engine, adv_params, adv_id):
    response = test_client.post("http://127.0.0.1:5000/advertisements/", json=adv_params)
    session = session_maker
    with session() as sess:
        sql_statement = sqlalchemy.text('SELECT * from "adv" WHERE id = :id')
        data_from_db = sess.execute(sql_statement, dict(id=adv_id)).first()
    assert response.status_code == 201
    assert response.json == {"advertisement id": adv_id}
    assert response.json["advertisement id"] == data_from_db[0]
    assert data_from_db[1] == adv_params["title"]
    assert data_from_db[2] == adv_params["description"]
    assert data_from_db[4] == adv_params["user_id"]


def test_get_user_data(test_client, session_maker):
    response = test_client.get("http://127.0.0.1:5000/users/1/")
    session = session_maker
    with session() as sess:
        data_from_db = \
            sess.execute(sqlalchemy.text('SELECT id, name, email, registration_date FROM "user" WHERE id = 1')).first()
    assert response.status_code == 200
    assert response.json == {"id": data_from_db[0],
                             "name": data_from_db[1],
                             "email": data_from_db[2],
                             "registration_date": data_from_db[3].isoformat()}


def test_get_adv_params(test_client, session_maker):
    response = test_client.get("http://127.0.0.1:5000/advertisements/1/")
    session = session_maker
    with session() as sess:
        data_from_db = sess.execute(sqlalchemy.text('SELECT * FROM "adv" WHERE id = 1')).first()
    assert response.status_code == 200
    assert response.json == {"id": data_from_db[0],
                             "title": data_from_db[1],
                             "description": data_from_db[2],
                             "creation_date": data_from_db[3].isoformat(),
                             "user_id": data_from_db[4]}


def test_update_user(test_client, session_maker):
    new_data = {"name": "new_name"}
    response = test_client.patch("http://127.0.0.1:5000/users/1/", json=new_data)
    session = session_maker
    with session() as sess:
        data_from_db = \
            sess.execute(sqlalchemy.text('SELECT id, name, email, registration_date FROM "user" WHERE id = 1')).first()
    assert response.status_code == 200
    assert response.json == {"modified user data": {"id": data_from_db[0],
                                                    "name": data_from_db[1],
                                                    "email": data_from_db[2],
                                                    "registration_date": data_from_db[3].isoformat()}}


def test_update_adv(test_client, session_maker):
    new_data = {"title": "new_title"}
    response = test_client.patch("http://127.0.0.1:5000/advertisements/1/", json=new_data)
    session = session_maker
    with session() as sess:
        data_from_db = sess.execute(sqlalchemy.text('SELECT * FROM "adv" WHERE id = 1')).first()
    assert response.status_code == 200
    assert response.json == {"modified advertisement params": {"id": data_from_db[0],
                                                               "title": data_from_db[1],
                                                               "description": data_from_db[2],
                                                               "creation_date": data_from_db[3].isoformat(),
                                                               "user_id": data_from_db[4]}}


def test_get_related_advs(test_client, session_maker):
    response = test_client.get("http://127.0.0.1:5000/users/1/advertisements/")
    session = session_maker
    with session() as sess:
        data_from_db = sess.execute(sqlalchemy.text('SELECT * FROM "adv" WHERE user_id = 1')).first()
    assert response.status_code == 200
    assert response.json == [{"id": data_from_db[0],
                              "title": data_from_db[1],
                              "description": data_from_db[2],
                              "creation_date": data_from_db[3].isoformat(),
                              "user_id": data_from_db[4]}]


def test_get_related_user(test_client, session_maker):
    response = test_client.get("http://127.0.0.1:5000/advertisements/1/user")
    session = session_maker
    with session() as sess:
        data_from_db = \
            sess.execute(sqlalchemy.text('SELECT id, name, email, registration_date FROM "user" WHERE id = 1')).first()
    assert response.status_code == 200
    assert response.json == {"id": data_from_db[0],
                             "name": data_from_db[1],
                             "email": data_from_db[2],
                             "registration_date": data_from_db[3].isoformat()}


def test_delete_user(test_client, session_maker):
    response = test_client.delete("http://127.0.0.1:5000/users/1/")
    session = session_maker
    with session() as sess:
        user_from_db = sess.execute(sqlalchemy.text('SELECT * FROM "user" WHERE id = 1')).first()
        related_adv_from_db = sess.execute(sqlalchemy.text('SELECT * FROM "adv" WHERE user_id = 1')).first()
    assert response.status_code == 200
    assert user_from_db is None
    assert related_adv_from_db is None


def test_delete_adv(test_client, session_maker):
    response = test_client.delete("http://127.0.0.1:5000/advertisements/2/")
    session = session_maker
    with session() as sess:
        data_from_db = sess.execute(sqlalchemy.text('SELECT * FROM "adv" WHERE id = 2')).first()
    assert response.status_code == 200
    assert data_from_db is None
