from typing import Protocol

import app.repository.repository
from app.models import session_maker
from app.repository.repository import Repository, UserRepository, AdvRepository


class UnitOfWork:
    def __init__(self):
        self.session_maker = session_maker

    def __enter__(self):
        self.session = self.session_maker()
        self.users = UserRepository(session=self.session)
        self.advs = AdvRepository(session = self.session)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.rollback()
            self.session.close()
        self.session.close()

    def rollback(self):
        self.session.rollback()

    def commit(self):
        self.session.commit()
