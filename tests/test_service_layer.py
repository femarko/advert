import datetime

import sqlalchemy, pytest

import app.errors
from app import pass_hashing, authentication, unit_of_work, validation, models
import app.authentication
from app import service_layer


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


def test_get_user_data(fake_check_current_user_func, fake_unit_of_work, fake_users_repo, fake_advs_repo, test_user):
    fuow = fake_unit_of_work(users=fake_users_repo([test_user]), advs=[])
    result = service_layer.get_user_data(user_id=1, check_current_user_func=fake_check_current_user_func, uow=fuow)
    expected_result = {
        "id": test_user.id,
        "name": test_user.name,
        "email": test_user.email,
        "creation_date": test_user.creation_date.isoformat()
    }
    assert result == expected_result


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
    data_from_repo = next(item for item in fuow.users.instances)
    assert type(result) is int
    assert 0 <= result <= 9
    assert result == data_from_repo.id
    assert data_from_repo.name == user_data["name"]
    assert data_from_repo.email == user_data["email"]
    assert data_from_repo.password == user_data["password"]
    assert data_from_repo.creation_date == user_data["creation_date"]


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
    assert uow.users.instances.pop().password == expected_password


def test_update_user_raises_not_found_error(
        fake_check_current_user_func, fake_validate_func, fake_hash_pass_func, fake_users_repo, fake_advs_repo,
        fake_unit_of_work
):
    new_data = {"name": "new_name", "email": "new_email", "password": "new_pass"}
    authenticated_user_id = 2
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
    with pytest.raises(app.errors.NotFoundError) as e:
        service_layer.update_user(
            authenticated_user_id=authenticated_user_id,
            check_current_user_func=fake_check_current_user_func,
            validate_func=fake_validate_func,
            hash_pass_func=fake_hash_pass_func,
            new_data=new_data,
            uow=uow
        )
    assert e.type == app.errors.NotFoundError


def test_get_related_advs(fake_check_current_user_func, fake_users_repo, fake_advs_repo, fake_unit_of_work):
    fusers_repo = fake_users_repo(users=[])
    fadvs_repo = fake_advs_repo(advs=[])
    fuow = fake_unit_of_work(users=fusers_repo, advs=fadvs_repo)
    result = service_layer.get_related_advs(
        authenticated_user_id=1, check_current_user_func=fake_check_current_user_func, uow=fuow
    )
    assert result == "FakeAdvsRepo: get_list_or_paginated_data() called."


def test_delete_user(fake_users_repo, fake_unit_of_work, fake_check_current_user_func, test_user):
    fusers_repo = fake_users_repo(users=[test_user])
    fuow = fake_unit_of_work(users=fusers_repo)
    users_before_deletion = fusers_repo.get(instance_id=test_user.id)
    deleted_user_params = service_layer.delete_user(
        user_id=test_user.id, check_current_user_func=fake_check_current_user_func, uow=fuow
    )
    users_after_deletion = fusers_repo.get(instance_id=test_user.id)
    assert users_before_deletion == test_user
    assert users_after_deletion == []
    assert deleted_user_params == test_user.get_params()


def test_delete_user_raises_not_found_error(
        fake_users_repo, fake_unit_of_work, fake_check_current_user_func, test_user
):
    fusers_repo = fake_users_repo(users=[test_user])
    fuow = fake_unit_of_work(users=fusers_repo)
    with pytest.raises(app.errors.NotFoundError):
        service_layer.delete_user(user_id=100, check_current_user_func=fake_check_current_user_func, uow=fuow)



