import sqlalchemy, pytest

import app.authentication
from app import service_layer, models
from tests.conftest import access_token


@pytest.mark.run(order=9)
def test_current_user_is_authorized(access_token):
    fake_user_id = 1
    app.authentication.check_current_user(user_id=fake_user_id)
    assert ...


def test_get_user(session_maker):
    session = session_maker
    email = "test_1@email.com"
    with session() as sess:
        user: models.User = service_layer.get_user(
            column="email",  # type: ignore
            column_value=email,
            session=sess)
    with session() as sess:
        expected = sess\
            .execute(sqlalchemy.text(f'SELECT * FROM "user" WHERE email = :email'), dict(email=email)).first()
    assert user.id == expected[0]
    assert user.name == expected[1]
    assert user.email == expected[2]
    assert user.password == expected[3]
    assert user.creation_date == expected[4]
