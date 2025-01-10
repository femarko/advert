import sqlalchemy, pytest

import app.authentication
from app import service_layer
from app.repository.filtering import FilterResult

# TODO: CurrentUserCheckFailedError is implemented in app.authentication.check_current_user() - refactoring needed.


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
