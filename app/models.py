from datetime import datetime
from sqlalchemy import create_engine, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship

POSTGRES_DSN = f"postgresql://adv:secret@127.0.0.1:5431/adv"

engine = create_engine(POSTGRES_DSN)

Session = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    pass


class User(Base):

    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    surname: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(100), unique=False, nullable=False, index=False)
    registration_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Advertisement(Base):

    __tablename__ = 'adv'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), unique=False, index=True, nullable=False)
    description: Mapped[str] = mapped_column(index=True, unique=False, nullable=False)
    creation_date: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    author: Mapped[str] = mapped_column(String(200))


Base.metadata.create_all(bind=engine)

