import pytest
import sqlalchemy

from app import service_layer, models


def test_retrieve_model_instance_correct_filter_params(session_maker):
    session = session_maker
    with session() as sess1:
        filter_params = {"email": "test_2@email.com"}
        user: models.User = service_layer.retrieve_model_instance(model_class=models.User,
                                                                  filter_params=filter_params,
                                                                  session=sess1)[0]
    session = session_maker
    with session() as sess2:
        data_from_db = \
            sess2.execute(sqlalchemy.text('SELECT id, name, email, registration_date FROM "user" WHERE id = 2')).first()
    assert user.id == data_from_db[0]
    assert user.name == data_from_db[1]
    assert user.email == data_from_db[2]
    assert user.registration_date.isoformat() == data_from_db[3].isoformat()


def test_retrieve_model_instance_incorrect_filter_params(session_maker):
    session = session_maker
    with session() as sess:
        filter_params = {"email": "incorrect@email.com"}
        user_list: list[models.User] = service_layer.retrieve_model_instance(model_class=models.User,
                                                                             filter_params=filter_params,
                                                                             session=sess)
    assert type(user_list) is list and not user_list
