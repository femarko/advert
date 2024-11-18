import pytest
import sqlalchemy

from app import adv, models


@pytest.fixture(scope="session")
def engine():
    return sqlalchemy.create_engine(models.POSTGRES_DSN)


@pytest.fixture
def session_maker(engine):
    return sqlalchemy.orm.sessionmaker(bind=engine)


@pytest.fixture(scope="session")
def drop_all_create_all(engine):
    models.Base.metadata.drop_all(bind=engine)
    models.Base.metadata.create_all(bind=engine)


@pytest.fixture
def test_client():
    return adv.test_client()


@pytest.fixture
def app_context():
    from app import adv
    return adv.app_context()


@pytest.fixture
def access_token(session_maker, app_context, test_client) -> dict[str, str]:
    access_token_dict = {}
    for i in range(1, 3):
        login_response = test_client\
            .post("http://127.0.0.1:5000/login/", json={"email": f"test_{i}@email.com",
                                                        "password": f"test_password_{i}"}).json
        access_token_dict[f"user_{i}"] = login_response.get("access_token")
    return access_token_dict
