import datetime

import sqlalchemy, pytest

import app.errors
from app import pass_hashing, authentication, unit_of_work, validation, models
import app.authentication
from app import service_layer


# @pytest.mark.run(order=9)
# def test_current_user_is_authorized(access_token):
#     fake_user_id = 1
#     app.authentication.check_current_user(user_id=fake_user_id)
#     assert ...
#
#
# def test_get_user(session_maker):
#     session = session_maker
#     email = "test_1@email.com"
#     with session() as sess:
#         filter_result: FilterResult = service_layer.get_users_list(
#             column="email", column_value=email, session=sess  # type: ignore
#         )
#     with session() as sess:
#         expected = sess \
#             .execute(sqlalchemy.text(f'SELECT * FROM "user" WHERE email = :email'), dict(email=email)).first()
#     assert filter_result.result[0].id == expected[0]
#     assert filter_result.result[0].name == expected[1]
#     assert filter_result.result[0].email == expected[2]
#     assert filter_result.result[0].password == expected[3]
#     assert filter_result.result[0].creation_date == expected[4]


def test_get_user_data(fake_check_current_user_func, fake_unit_of_work, fake_users_repo, fake_advs_repo,
                       fake_validate_func, fake_hash_pass_func, test_date):
    user_data = {
        "name": "test_name", "email": "test_email@test.com", "password": "test_pass", "creation_date": test_date
    }
    fusers_repo = fake_users_repo(users=[])
    fuow = fake_unit_of_work(users=fusers_repo)
    user_id: int = service_layer.create_user(
        user_data=user_data, validate_func=fake_validate_func, hash_pass_func=fake_hash_pass_func, uow=fuow
    )
    result = service_layer.get_user_data(
        user_id=user_id, check_current_user_func=fake_check_current_user_func, uow=fuow
    )
    expected_result = {
        "id": user_id,
        "name": user_data["name"],
        "email": user_data["email"],
        "creation_date": test_date.isoformat()
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


def test_update_user(fake_check_current_user_func, fake_validate_func, fake_hash_pass_func, fake_users_repo,
                     fake_advs_repo, fake_unit_of_work, test_date):
    new_data = {"name": "new_name", "email": "new_email", "password": "new_pass"}
    user_data = {
        "name": "test_name", "email": "test_email@test.com", "password": "test_pass", "creation_date": test_date
    }
    fusers_repo = fake_users_repo(users=[])
    fuow = fake_unit_of_work(users=fusers_repo)
    user_id: int = service_layer.create_user(
        user_data=user_data, validate_func=fake_validate_func, hash_pass_func=fake_hash_pass_func, uow=fuow
    )
    uow = fake_unit_of_work(users=fusers_repo)
    expected_result = {"id": user_id, "creation_date": test_date.isoformat(), **new_data}
    expected_password = expected_result.pop("password")
    result = service_layer.update_user(
        user_id=user_id,
        check_current_user_func=fake_check_current_user_func,
        validate_func=fake_validate_func,
        hash_pass_func=fake_hash_pass_func,
        new_data=new_data,
        uow=uow
    )
    assert result == expected_result
    assert uow.users.instances.pop().password == expected_password


def test_get_related_advs(fake_check_current_user_func, fake_users_repo, fake_advs_repo, fake_unit_of_work):
    fusers_repo = fake_users_repo(users=[])
    fadvs_repo = fake_advs_repo(advs=[])
    fuow = fake_unit_of_work(users=fusers_repo, advs=fadvs_repo)
    result = service_layer.get_related_advs(
        authenticated_user_id=1, check_current_user_func=fake_check_current_user_func, uow=fuow
    )
    assert result == "FakeAdvsRepo: get_list_or_paginated_data() called."


def test_delete_user(fake_users_repo, fake_unit_of_work, fake_check_current_user_func, fake_validate_func,
                     fake_hash_pass_func, test_user):
    user_data = {"name": "test_name", "email": "test_email@test.com", "password": "test_pass"}
    fusers_repo = fake_users_repo(users=[])
    fuow = fake_unit_of_work(users=fusers_repo)
    user_id: int = service_layer.create_user(
        user_data=user_data, validate_func=fake_validate_func, hash_pass_func=fake_hash_pass_func, uow=fuow
    )
    user_before_deletion = fusers_repo.get(instance_id=user_id)
    deleted_user_params = service_layer.delete_user(
        user_id=user_id, check_current_user_func=fake_check_current_user_func, uow=fuow
    )
    users_after_deletion = fusers_repo.get(instance_id=user_id)
    assert users_after_deletion == []
    assert deleted_user_params == user_before_deletion.get_params()


def test_delete_user_raises_not_found_error(fake_users_repo, fake_unit_of_work, fake_check_current_user_func,
                                            fake_validate_func, fake_hash_pass_func, test_date):
    user_data = {
        "name": "test_name", "email": "test_email@test.com", "password": "test_pass", "creation_date": test_date
    }
    fusers_repo = fake_users_repo(users=[])
    fuow = fake_unit_of_work(users=fusers_repo)
    user_id: int = service_layer.create_user(
        user_data=user_data, validate_func=fake_validate_func, hash_pass_func=fake_hash_pass_func, uow=fuow
    )
    uow = fake_unit_of_work(users=fusers_repo)
    with pytest.raises(app.errors.NotFoundError):
        service_layer.delete_user(user_id=user_id+1, check_current_user_func=fake_check_current_user_func, uow=uow)


def test_create_adv(fake_get_auth_user_id_func, fake_validate_func, fake_hash_pass_func, fake_users_repo,
                    fake_advs_repo, fake_unit_of_work, test_date, fake_check_current_user_func):
    user_data = {"id": 1, "name": "test_name", "email": "test_email@test.com", "password": "test_pass",
                 "creation_date": test_date}
    fusers_repo, fadvs_repo = fake_users_repo(users=[]), fake_advs_repo(advs=[])
    fuow = fake_unit_of_work(users=fusers_repo, advs=fadvs_repo)
    user_id: int = service_layer.create_user(
        user_data=user_data, validate_func=fake_validate_func, hash_pass_func=fake_hash_pass_func, uow=fuow
    )
    adv_params = {"title": "test_title", "description": "test_description"}
    fuow2 = fake_unit_of_work(advs=fake_advs_repo([]))
    result = service_layer.create_adv(
        get_auth_user_id_func=fake_get_auth_user_id_func, adv_params=adv_params, validate_func=fake_validate_func,
        check_current_user_func=fake_check_current_user_func, uow=fuow2
    )
    data_from_repo = fuow2.advs.get(instance_id=result)
    assert isinstance(result, int)
    assert 0 <= result <= 9
    assert result == data_from_repo.id
    assert data_from_repo.title == adv_params["title"]
    assert data_from_repo.description == adv_params["description"]
    assert data_from_repo.creation_date == test_date
    assert data_from_repo.user_id == user_id


def test_get_adv(fake_users_repo, fake_advs_repo, fake_unit_of_work, fake_check_current_user_func, fake_validate_func,
                 fake_hash_pass_func, fake_get_auth_user_id_func, test_date):
    user_data = {"id": 1, "name": "test_name", "email": "test_email@test.com", "password": "test_pass"}
    fusers_repo, fadvs_repo = fake_users_repo(users=[]), fake_advs_repo(advs=[])
    fuow = fake_unit_of_work(users=fusers_repo, advs=fadvs_repo)
    user_id: int = service_layer.create_user(
        user_data=user_data, validate_func=fake_validate_func, hash_pass_func=fake_hash_pass_func, uow=fuow
    )
    adv_params = {"title": "test_title", "description": "test_description", "creation_date": test_date}
    fuow2 = fake_unit_of_work(advs=fake_advs_repo([]))
    adv_id = service_layer.create_adv(
        get_auth_user_id_func=fake_get_auth_user_id_func, adv_params=adv_params, validate_func=fake_validate_func,
        check_current_user_func=fake_check_current_user_func, uow=fuow2
    )
    result = service_layer.get_adv(adv_id=adv_id, check_current_user_func=fake_check_current_user_func, uow=fuow2)
    expected_result = {"id": adv_id, "user_id": user_id, **adv_params}
    assert result.id == expected_result["id"]
    assert result.title == expected_result["title"]
    assert result.user_id == expected_result["user_id"]
    assert result.description == expected_result["description"]
    assert result.creation_date == expected_result["creation_date"]


def test_get_adv_raises_not_found_error(fake_check_current_user_func, fake_advs_repo, fake_unit_of_work):
    uow = fake_unit_of_work(advs=fake_advs_repo(advs=[]))
    with pytest.raises(expected_exception=app.errors.NotFoundError) as e:
        service_layer.get_adv(adv_id=1, check_current_user_func=fake_check_current_user_func, uow=uow)
    assert e.value.message == "The advertisement with the provided parameters is not found."
