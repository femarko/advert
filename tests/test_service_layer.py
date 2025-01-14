import datetime

import sqlalchemy, pytest

from app import pass_hashing, authentication, unit_of_work, validation, models
import app.authentication
from app import service_layer
from app.repository.filtering import FilterResult
# from tests import fakes


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
        expected = sess \
            .execute(sqlalchemy.text(f'SELECT * FROM "user" WHERE email = :email'), dict(email=email)).first()
    assert filter_result.result[0].id == expected[0]
    assert filter_result.result[0].name == expected[1]
    assert filter_result.result[0].email == expected[2]
    assert filter_result.result[0].password == expected[3]
    assert filter_result.result[0].creation_date == expected[4]


def test_update_user(
        fake_check_current_user_func, fake_validate_func, fake_hash_pass_func, fake_users_repo, fake_advs_repo,
        fake_unit_of_work
):
    new_data = {"name": "new_name", "email": "new_email", "password": "new_pass"}
    authenticated_user_id = 1
    creation_date = datetime.datetime.today()
    user = models.User(
        id=1,
        name="test_name",
        email="test_email",
        password="test_pass",
        creation_date=creation_date,
        advertisements=[]
    )
    uow = fake_unit_of_work(users=fake_users_repo([user]), advs=fake_advs_repo([]))
    expected_result = {"id": 1, "creation_date": creation_date.isoformat(), **new_data}
    expected_password = expected_result.pop("password")
    result = service_layer.update_user(
        authenticated_user_id=authenticated_user_id,
        check_current_user_func=fake_check_current_user_func,
        validate_func=fake_validate_func,
        hash_pass_func=fake_hash_pass_func,
        new_data=new_data,
        uow=uow
    )
    assert result == expected_result
    assert uow.users.users.pop().password == expected_password
