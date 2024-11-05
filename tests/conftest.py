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
def base_url():
    return "http://127.0.0.1:5000/"
