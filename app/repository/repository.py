from typing import Callable, Any


class Repository:
    def __init__(self, session):
        self.session = session

    def add(self, model_instance):
        self.session.add(model_instance)

    def get_list(self, filter_func: Callable, **params: Any):
        return filter_func(session=self.session, **params)

    def get_paginated(self, filter_func: Callable, **params: Any):
        return filter_func(session=self.session, **params)

    def delete(self, model_instance):
        self.session.delete(model_instance)
