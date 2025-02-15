from datetime import datetime
from typing import Any, Protocol, Optional

from sqlalchemy.exc import IntegrityError

import app.domain.errors
import app.service_layer.app_manager
from app.domain.models import User, Advertisement, UserColumns, AdvertisementColumns
from app.repository import filtering
from app.repository.filtering import FilterTypes, Comparison


class NotFoundError(Exception):
    pass


class RepoProto(Protocol):
    def add(self, instance) -> None:
        pass

    def get(self, instance_id: int) -> Any:
        pass

    def get_list_or_paginated_data(self,
                                   filter_type: FilterTypes,
                                   comparison: Comparison,
                                   column: UserColumns | AdvertisementColumns,
                                   column_value: int | str| datetime,
                                   paginate: Optional[bool] = False,
                                   page: Optional[int] = None,
                                   per_page: Optional[int] = None) -> list | dict:
        pass

    def delete(self, instance) -> None:
        pass


class Repository:
    def __init__(self, session):
        self.session = session
        self.model_cl = None

    def add(self, instance) -> None:
        try:
            self.session.add(instance)
        except IntegrityError:
            raise app.domain.errors.AlreadyExistsError

    def get(self, instance_id: int) -> Any:
        return self.session.get(self.model_cl, instance_id)

    def get_list_or_paginated_data(self,
                                   filter_type: FilterTypes,
                                   comparison: Comparison,
                                   column: UserColumns | AdvertisementColumns,
                                   column_value: int | str| datetime,
                                   paginate: Optional[bool] = False,
                                   page: Optional[int] = None,
                                   per_page: Optional[int] = None) -> list | dict:
        return filtering.get_list_or_paginated_data(
            session=self.session,
            model_class=self.model_cl,
            filter_type=filter_type,
            comparison=comparison,
            column=column,
            column_value=column_value,
            paginate=paginate,
            page=page,
            per_page=per_page
        )

    def delete(self, instance) -> None:
        self.session.delete(instance)


class UserRepository(Repository):
    def __init__(self, session):
        super().__init__(session=session)
        self.model_cl = User


class AdvRepository(Repository):
    def __init__(self, session):
        super().__init__(session=session)
        self.model_cl = Advertisement
