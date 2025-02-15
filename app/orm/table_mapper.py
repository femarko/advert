import sqlalchemy
from sqlalchemy import Table, Column, Integer, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship

import app.domain.models


mapper = sqlalchemy.orm.registry()

user_table = Table(
    "user",
    mapper.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String(200), nullable=False),
    Column("email", String(40), nullable=False, unique=True, index=True),
    Column("password", String(200), nullable=False),
    Column("creation_date", DateTime, server_default=func.now())
)


adv_table = Table(
    "adv",
    mapper.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("title", String(200), index=True, nullable=False),
    Column("description", String, index=True),
    Column("creation_date", DateTime, server_default=func.now()),
    Column("user_id", Integer, ForeignKey("user.id"), nullable=False)
)


def start_mapping():
    mapper.map_imperatively(
        class_=app.domain.models.User, local_table=user_table, properties={
            "adv": relationship(
                app.domain.models.Advertisement, backref="user", order_by=adv_table.c.id, cascade="delete"
            )
        }
    )
    mapper.map_imperatively(class_=app.domain.models.Advertisement, local_table=adv_table)
