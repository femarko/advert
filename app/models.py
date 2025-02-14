import enum
from datetime import datetime
from typing import TypeVar, Optional

from sqlalchemy import create_engine, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship

from app.error_handlers import HttpError

POSTGRES_DSN = f"postgresql://adv:secret@127.0.0.1:5431/adv"
engine = create_engine(POSTGRES_DSN)
session_maker = sessionmaker(bind=engine)


class Base:
    pass


class User:
    def __init__(
            self, name: str, email: str, password: str, id: Optional[int] = None,
            creation_date: Optional[datetime] = None
    ):
        self.id = id
        self.name = name
        self.email = email
        self.password = password
        self.creation_date = creation_date

    def get_params(self) -> dict[str, str | int | datetime]:
        return {"id": self.id,
                "name": self.name,
                "email": self.email,
                "creation_date": self.creation_date.isoformat()}


class Advertisement:
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

    def get_params(self) -> dict[str, str | int]:
        return {"id": self.id,
                "title": self.title,
                "description": self.description,
                "creation_date": self.creation_date.isoformat(),
                "user_id": self.user_id}

    # def get_related_user(self):
    #     return self.user.get_user_data()


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