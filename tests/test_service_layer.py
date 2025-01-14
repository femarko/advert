import sqlalchemy, pytest

from app import pass_hashing, authentication, unit_of_work, validation
import app.authentication
from app import service_layer
from app.repository.filtering import FilterResult
from tests.fakes import fake_check_current_user_func


@pytest.mark.run(order=9)
def test_current_user_is_authorized(access_token):
    fake_user_id = 1
    app.authentication.check_current_user(user_id=fake_user_id)
    assert ...


def test_get_user(session_maker):
    session = session_maker
    email = "test_1@email.com"
    with session() as sess:
        filter_result: FilterResult = service_layer.get_users_list(
            column="email", column_value=email, session=sess  # type: ignore
        )
    with session() as sess:
        expected = sess\
            .execute(sqlalchemy.text(f'SELECT * FROM "user" WHERE email = :email'), dict(email=email)).first()
    assert filter_result.result[0].id == expected[0]
    assert filter_result.result[0].name == expected[1]
    assert filter_result.result[0].email == expected[2]
    assert filter_result.result[0].password == expected[3]
    assert filter_result.result[0].creation_date == expected[4]


def test_update_user(create_test_users_and_advs, session_maker):
    new_data = {"name": "new_name", "email": "new_email", "password": "new_pass"}
    authenticated_user_id = 1000
    check_current_user_func = fake_check_current_user_func
    validate_func = validation.validate_data_for_user_updating
    hash_pass_func = pass_hashing.hash_password
    uow = unit_of_work.UnitOfWork()
    expected = {"id": 1000,
                "name": "new_name",
                "email": "new_email"}
    result = service_layer.update_user(authenticated_user_id=authenticated_user_id,
                                       check_current_user_func=check_current_user_func,
                                       validate_func=validate_func,
                                       hash_pass_func=hash_pass_func,
                                       new_data=new_data,
                                       uow=uow)
    session = session_maker()
    with session as sess:
        data_from_db = \
            sess.execute(sqlalchemy.text('SELECT * from "user" WHERE id = :id'), dict(id=authenticated_user_id)).first()
    assert result["id"] == expected["id"] == data_from_db[0]
    assert result["name"] == expected["name"] == data_from_db[1]
    assert result["email"] == expected["email"] == data_from_db[2]
    assert pass_hashing.check_password(hashed_password=data_from_db[3], password=new_data["password"])
