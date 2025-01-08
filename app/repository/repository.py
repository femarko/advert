from typing import Callable, Any, Protocol
from .filtering import Filter, FilterResult, filter_and_return_list, filter_and_return_paginated_data
from app.models import User, Advertisement


class NotFound(Exception):
    pass


class Repository(Protocol):
    def __init__(self, session):
        self.session = session

    def add(self, model_instance):
        pass

    def get(self, **kwargs):
        return self.session.get(**kwargs)

    def get_list(self, **params: Any):
        pass

    def get_paginated(self, **params: Any):
        pass

    def delete(self, model_instance):
        pass


class UserRepository:
    def __init__(self, session):
        self.session = session
        self.model_cl = User

    def add(self, user_instance):
        return self.session.add(user_instance)

    def get(self, user_id: int):
        user_instance = self.session.get(self.model_cl, user_id)
        if user_instance is not None:
            return user_instance
        raise NotFound(f"User with id {user_id} is not found.")

    def get_list(self, filter_type, comparison, column, column_value) -> FilterResult:
        filter_result = filter_and_return_list(session=self.session,
                                               model_class=self.model_cl,
                                               filter_type=filter_type,
                                               comparison=comparison,
                                               column=column,
                                               column_value=column_value)
        return filter_result

    def get_paginated(self, filter_type, column, column_value, comparison, page, per_page) -> FilterResult:
        filter_res = filter_and_return_paginated_data(session=self.session,
                                                      model_class=self.model_cl,
                                                      filter_type=filter_type,
                                                      column=column,
                                                      column_value=column_value,
                                                      comparison=comparison,
                                                      page=page,
                                                      per_page=per_page)
        return filter_res

    def delete(self, user_instance):
        self.session.delete(user_instance)


class AdvRepository:
    def __init__(self, session):
        self.session = session
        self.model_cl = Advertisement

    def add(self, adv_instance):
        return self.session.add(adv_instance)

    def get(self, adv_instance, adv_id):
        return self.session.get(adv_instance, adv_id)

    def get_list(self, filter_type, comparison, column, column_value) -> FilterResult:
        filter_result = filter_and_return_list(session=self.session,
                                               model_class=self.model_cl,
                                               filter_type=filter_type,
                                               comparison=comparison,
                                               column=column,
                                               column_value=column_value)
        return filter_result

    def get_paginated(self, filter_type, column, column_value, comparison, page, per_page) -> FilterResult:
        filter_result = filter_and_return_paginated_data(session=self.session,
                                                         model_class=self.model_cl,
                                                         filter_type=filter_type,
                                                         column=column,
                                                         column_value=column_value,
                                                         comparison=comparison,
                                                         page=page,
                                                         per_page=per_page)
        return filter_result

    def delete(self, adv_instance):
        self.session.delete(adv_instance)
