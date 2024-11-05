from datetime import datetime
from sqlalchemy import create_engine, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship

from app.error_handlers import HttpError

POSTGRES_DSN = f"postgresql://adv:secret@127.0.0.1:5431/adv"

engine = create_engine(POSTGRES_DSN)

Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(100), nullable=False, index=False)
    registration_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    advertisements: Mapped[list["Advertisement"]] = relationship(back_populates="user", cascade="delete")

    def get_user_data(self) -> dict[str, str | int | datetime]:
        return {"id": self.id,
                "name": self.name,
                "email": self.email,
                "registration_date": self.registration_date.isoformat()}

    def get_user_advs(self) -> list[dict[str, str | int | datetime]]:
        return [adv.get_adv_params() for adv in self.advertisements]


class Advertisement(Base):
    __tablename__ = 'adv'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), unique=False, index=True, nullable=False)
    description: Mapped[str] = mapped_column(index=True, unique=False, nullable=False)
    creation_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"))
    user: Mapped[User] = relationship(back_populates="advertisements")

    def __repr__(self):
        return f'{self.title}\n{self.description}'

    def get_adv_params(self) -> dict[str, str | int | datetime]:
        return {"id": self.id,
                "title": self.title,
                "description": self.description,
                "creation_date": self.creation_date.isoformat(),
                "user_id": self.user_id}

    def get_related_user(self):
        return self.user.get_user_data()


Base.metadata.create_all(bind=engine)
