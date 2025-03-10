import datetime
from typing import Optional

import pytest
import sqlalchemy

import app.orm
import app.pass_hashing_and_validation.pass_hashing, app.domain.errors
from app.flask_entrypoints import adv
from app.orm import table_mapper
from app.domain import services


@pytest.fixture(scope="session")
def engine():
    return sqlalchemy.create_engine(app.orm.POSTGRES_DSN)


@pytest.fixture
def session_maker(engine):
    return sqlalchemy.orm.sessionmaker(bind=engine)


@pytest.fixture
def clear_db_before_and_after_test(engine):
    table_mapper.mapper.metadata.drop_all(bind=engine)
    table_mapper.mapper.metadata.create_all(bind=engine)
    yield
    table_mapper.mapper.metadata.drop_all(bind=engine)
    table_mapper.mapper.metadata.create_all(bind=engine)


@pytest.fixture
def test_client():
    return adv.test_client()


@pytest.fixture
def app_context():
    from app.flask_entrypoints import adv
    return adv.app_context()


@pytest.fixture
def test_date():
    return datetime.datetime(1900, 1, 1)


@pytest.fixture
def create_test_users_and_advs(session_maker, test_date):
    session = session_maker
    with session() as sess:
        for i in range(1000, 1002):
            sess.execute(sqlalchemy.text('INSERT INTO "user" (id, name, email, password, creation_date) '
                                         'VALUES (:id, :name, :email, :password, :creation_date)'),
                         dict(id=i,
                              name=f"test_filter_{i}",
                              email=f"test_filter_{i}@email.com",
                              password=app.pass_hashing_and_validation.pass_hashing.hash_password(
                                  f"test_filter_{i}_pass"
                              ),
                              creation_date=test_date))
            sess.execute(sqlalchemy.text('INSERT INTO "adv" (id, title, description, creation_date, user_id) '
                                         'VALUES (:id, :title, :description, :creation_date, :user_id)'),
                         dict(id=i,
                              title=f"test_filter_{i}",
                              description=f"test_filter_{i}",
                              creation_date=test_date,
                              user_id=i))
            sess.execute(sqlalchemy.text('INSERT INTO "adv" (id, title, description, creation_date, user_id) '
                                         'VALUES (:id, :title, :description, :creation_date, :user_id)'),
                         dict(id=i + 3,
                              title=f"test_filter_{i + 3}",
                              description=f"test_filter_{i + 3}",
                              creation_date=test_date,
                              user_id=i))
            sess.commit()
    yield
    with session() as sess:
        sess.execute(sqlalchemy.text('DELETE FROM "adv" WHERE (creation_date = :creation_date)'),
                     dict(creation_date=test_date))
        sess.execute(sqlalchemy.text('DELETE FROM "user" WHERE (creation_date = :creation_date)'),
                     dict(creation_date=test_date))
        sess.commit()


def return_func_deco(func):
    def wrapper():
        return func
    return wrapper


@pytest.fixture(scope="function")
@return_func_deco
def fake_get_auth_user_id_func():
    return 1


@pytest.fixture
@return_func_deco
def fake_get_auth_user_id_func_2():
    return 2


@pytest.fixture(scope="function")
@return_func_deco
def fake_check_current_user_func(user_id: int, get_cuid: bool = True):
    return user_id


@pytest.fixture(scope="function")
@return_func_deco
def fake_validate_func(**data):
    return data


@pytest.fixture(scope="function")
@return_func_deco
def fake_hash_pass_func(password: str):
    return password


@pytest.fixture(scope="function")
def fake_users_repo():
    return FakeUsersRepo


@pytest.fixture(scope="function")
def fake_advs_repo():
    return FakeAdvsRepo


@pytest.fixture(scope="function")
def fake_unit_of_work():
    return FakeUnitOfWork


class FakeBaseRepo:
    def __init__(self, instances: list):
        self.instances: set = set(instances)
        self.temp_added = []
        self.temp_deleted = []

    def add(self, instance):
        self.temp_added.append(instance)

    def get(self, instance_id):
        if instance_id not in (instance.id for instance in self.instances):
            return []
        return next(instance for instance in self.instances if instance.id == instance_id)

    def get_list_or_paginated_data(self, paginate: Optional[bool] = False, **kwargs):
        if paginate:
            return {"items": [services.get_params(model=item) for item in self.instances]}
        return f"{self.__str__()}: get_list_or_paginated_data() called."

    def delete(self, instance):
        self.temp_deleted.append(instance)

    def execute_adding(self):
        for item in self.temp_added:
            if not item.id:
                item.id = 1
            if not item.creation_date:
                item.creation_date = datetime.datetime(1900, 1, 1)
            self.instances.add(item)
        self.temp_added = []

    def execute_deletion(self):
        for item in self.temp_deleted:
            self.instances.remove(item)
        self.temp_deleted = []


class FakeUsersRepo(FakeBaseRepo):
    def __init__(self, users: list):
        super().__init__(instances=users)

    def __str__(self):
        return "FakeUsersRepo"


class FakeAdvsRepo(FakeBaseRepo):
    def __init__(self, advs: list):
        super().__init__(instances=advs)

    def __str__(self):
        return "FakeAdvsRepo"


class FakeUnitOfWork:
    def __init__(self, users: Optional[FakeUsersRepo] = None, advs: Optional[FakeAdvsRepo] = None):
        self.users = users
        self.advs = advs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()

    def rollback(self):
        pass

    def commit(self):
        if self.users and self.users.temp_added:
            self.users.execute_adding()
        if self.advs and self.advs.temp_added:
            self.advs.execute_adding()
        if self.users and self.users.temp_deleted:
            self.users.execute_deletion()
        if self.advs and self.advs.temp_deleted:
            self.advs.execute_deletion()


@pytest.fixture
def test_user_data():
    return {"name": "test_name", "email": "test@email.test", "password": "test_pass"}


@pytest.fixture
def test_adv_params(test_user_data):
    return {"title": "test_title", "description": "test_description", "user_id": 1}
