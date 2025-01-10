from typing import Callable, Any, Protocol
from app.models import User, Advertisement


class NotFoundError(Exception):
    pass


class RepoProt(Protocol):
    def add(self, instance) -> None:
        pass

    def get(self, instance_id) -> None:
        pass

    def get_list_or_paginated_data(self, filter_func: Callable, **kwargs: Any) -> list | dict:
        pass

    def delete(self, instance) -> None:
        pass


class Repository:
    def __init__(self, session):
        self.session = session
        self.model_cl = None

    def add(self, instance):
        self.session.add(instance)

    def get(self, instance_id):
        instance = self.session.get(self.model_cl, instance_id)
        if instance is not None:
            return instance
        raise NotFoundError(f"{instance} with id {instance_id} is not found.")

    def get_list_or_paginated_data(self, filter_func: Callable, **kwargs: Any):
        return filter_func(self.session, model_class=self.model_cl, **kwargs)

    def delete(self, instance):
        self.session.delete(instance)


class UserRepository(Repository):
    def __init__(self, session):
        super().__init__(session=session)
        self.model_cl = User


class AdvRepository(Repository):
    def __init__(self, session):
        super().__init__(session=session)
        self.model_cl = Advertisement
