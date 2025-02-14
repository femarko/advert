import enum
from datetime import datetime
from typing import TypeVar, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


POSTGRES_DSN = f"postgresql://adv:secret@127.0.0.1:5431/adv"
engine = create_engine(POSTGRES_DSN)
session_maker = sessionmaker(bind=engine)


class Base:
    pass


class User(Base):
    def __init__(
            self, name: str, email: str, password: str, id: Optional[int] = None,
            creation_date: Optional[datetime] = None
    ):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.creation_date = creation_date


class Advertisement(Base):
    def __init__(
            self, title: str, description: str, user_id: int, id: Optional[int] = None,
            creation_date: Optional[datetime] = None
    ):
        self.id = id
        self.title = title
        self.description = description
        self.user_id = user_id
        self.creation_date = creation_date

    def __repr__(self):
        return f'{self.title}\n{self.description}'


class Model(str, enum.Enum):
    USER = "user"
    ADVERTISEMENT = "advertisement"


class ModelClasses(enum.Enum):
    USER = User
    ADV = Advertisement


class AdvertisementColumns(str, enum.Enum):
    ID = "id"
    TITLE = "title"
    DESCRIPTION = "description"
    CREATION_DATE = "creation_date"
    USER_ID = "user_id"


class UserColumns(str, enum.Enum):
    ID = "id",
    NAME = "name"
    EMAIL = "email"
    CREATION_DATE = "creation_date"


ModelClass = TypeVar("ModelClass", bound=Base)
