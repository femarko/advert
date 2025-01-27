import enum
import sqlalchemy
from dataclasses import dataclass
from datetime import datetime
from typing import Type, Literal, Any

from sqlalchemy.orm import Query

import app.errors
from app.models import AdvertisementColumns, UserColumns, ModelClass, User, Advertisement, ModelClasses


class InvalidFilterParams(Exception):
    pass


class FilterTypes(str, enum.Enum):
    COLUMN_VALUE = "column_value"
    SEARCH_TEXT = "search_text"


class Comparison(str, enum.Enum):
    IS = "is"
    NOT = "is_not"
    LT = "<"
    GT = ">"
    GE = ">="
    LE = "<="


class Params(str, enum.Enum):
    MODEL_CLASS = "model_class"
    FILTER_TYPE = "filter_type"
    COLUMN = "column"
    COLUMN_VALUE = "column_value"
    COMPARISON = "comparison"


class ValidParams(enum.Enum):
    MODEL_CLASS = [mc.value for mc in ModelClasses]
    FILTER_TYPE = [ft.value for ft in FilterTypes]
    COLUMN_USER = [c.value for c in UserColumns]
    COLUMN_ADV = [c.value for c in AdvertisementColumns]
    COMPARISON = [cmp.value for cmp in Comparison]


# @dataclass
# class QueryBase:
#     # status: Literal["OK", "Failed"] = "OK"
#     errors: set[str] | list[str] | None = None


# @dataclass
# class QueryResult(QueryBase):
#     result: sqlalchemy.orm.Query | None = None


# @dataclass
# class FilterResult(QueryBase):
#     result: list[ModelClass] | dict[str, int | list[ModelClass]] | None = None


class Filter:

    def __init__(self, session: sqlalchemy.orm.Session, ):
        self.session = session
        self._comparison = {"is": {"apply": "__eq__", "explain": "Equal to"},
                            "is_not": {"apply": "__ne__", "explain": "Not equal to"},
                            "<": {"apply": "__lt__", "explain": "Less than"},
                            "<=": {"apply": "__le__", "explain": "Less than or equal to"},
                            ">": {"apply": "__gt__", "explain": "Greater than"},
                            ">=": {"apply": "__ge__", "explain": "Greater than or equal to"}}
        self.query_filtered: Query | None = None
        self.res_list: list | None = None
        self.paginated: dict | None = None
        self.errors: set[str] = set()

    def _add_error(self,
                   param: Params | None = None,
                   invalid_value: Any = None,
                   valid_values: list[Any] | dict[str, Any] | None = None,
                   comment: str | None = None) -> None:
        if invalid_value is None and not comment:
            self.errors.add(f"Value for '{param}' is not found.")
        elif comment:
            self.errors.add(comment)
        else:
            self.errors.add(f"'{invalid_value}' is invalid value for '{param}'. Valid values: {valid_values}.")

    def _validate_params(self, data: dict[str, Any], params: Type[Params]) -> None:
        data_dict = {}
        for param in params:
            data_dict |= {param.value: data.get(param.value)}  # type: ignore
        if data_dict[Params.MODEL_CLASS] not in [mc.value for mc in ModelClasses]:
            self._add_error(Params.MODEL_CLASS, data_dict[Params.MODEL_CLASS], ValidParams.MODEL_CLASS.value)
        if data_dict[Params.FILTER_TYPE] not in ValidParams.FILTER_TYPE.value:
            self._add_error(Params.FILTER_TYPE, data_dict[Params.FILTER_TYPE], ValidParams.FILTER_TYPE.value)
        if data_dict[Params.COLUMN] not in set(ValidParams.COLUMN_USER.value + ValidParams.COLUMN_ADV.value) \
                and data_dict[Params.MODEL_CLASS] not in [mc.value for mc in ModelClasses]:
            self._add_error(
                Params.COLUMN, data_dict[Params.COLUMN], {f"for {User}": ValidParams.COLUMN_USER.value,
                                                          f"for {Advertisement}": ValidParams.COLUMN_ADV.value}
            )
        if data_dict[Params.COMPARISON] not in ValidParams.COMPARISON.value \
                and data_dict[Params.FILTER_TYPE] != FilterTypes.SEARCH_TEXT:
            self._add_error(Params.COMPARISON, data_dict[Params.COMPARISON], ValidParams.COMPARISON.value)
        match data_dict[Params.COLUMN], data_dict[Params.COLUMN_VALUE]:
            case column, column_value if \
                    column in [UserColumns.ID, AdvertisementColumns.ID, AdvertisementColumns.USER_ID] \
                    and ((type(column_value) is str and not column_value.isdigit()) and type(column_value) is not int):
                self._add_error(comment=f"'{column}' must be a digit.")
            case column, column_value if \
                    column in [UserColumns.CREATION_DATE, AdvertisementColumns.CREATION_DATE] \
                    and type(column_value) is str:
                try:
                    datetime.strptime(column_value, "%Y-%m-%d")
                except (ValueError, TypeError):
                    self._add_error(comment=f"When {column=}, '{Params.COLUMN_VALUE}' must be a date string "
                                            f"of the following format: 'YYYY-MM-DD'.")
            case column, column_value if column in [UserColumns.CREATION_DATE, AdvertisementColumns.CREATION_DATE] \
                    and type(column_value) is not str:
                self._add_error(comment=f"When {column=}, '{Params.COLUMN_VALUE}' must be a date string "
                                        f"of the following format: 'YYYY-MM-DD'.")
            case *_, :
                pass
        match data_dict[Params.FILTER_TYPE], data_dict[Params.COLUMN], data_dict[Params.COMPARISON]:
            case filter_type, column, comparison if filter_type == FilterTypes.COLUMN_VALUE and column in \
                    [UserColumns.NAME, UserColumns.EMAIL, AdvertisementColumns.TITLE, AdvertisementColumns.DESCRIPTION]\
                    and comparison in [Comparison.LE, Comparison.LT, Comparison.GE, Comparison.GT]:
                self._add_error(Params.COMPARISON, comparison, [Comparison.IS.value, Comparison.NOT.value])
            case filter_type, column, _ if filter_type == FilterTypes.SEARCH_TEXT and column not in \
                    [UserColumns.NAME, UserColumns.EMAIL, AdvertisementColumns.TITLE, AdvertisementColumns.DESCRIPTION]:
                self._add_error(comment=f"For {filter_type=} the folowing columns are available: "
                                        f"{{for {User}: [{UserColumns.NAME}, {UserColumns.EMAIL}], "
                                        f"for {Advertisement}: "
                                        f"[{AdvertisementColumns.TITLE}, {AdvertisementColumns.DESCRIPTION}]}}")
            case *_, :
                pass
        match data_dict[Params.COLUMN], data_dict[Params.MODEL_CLASS]:
            case column, model_class if model_class == User and column not in ValidParams.COLUMN_USER.value:
                self._add_error(Params.COLUMN, column, ValidParams.COLUMN_USER.value)
            case column, model_class if model_class == Advertisement and column not in ValidParams.COLUMN_ADV.value:
                self._add_error(Params.COLUMN, column, ValidParams.COLUMN_ADV.value)
            case *_, :
                pass
        if self.errors:
            raise app.errors.ValidationError(list(self.errors))

    def get_filter_result(self,
                          model_class: Type[User | Advertisement] | None = None,
                          filter_type: FilterTypes | None = None,
                          column: AdvertisementColumns | UserColumns | None = None,
                          column_value: str | None = None,
                          comparison: Comparison | None = None,
                          paginate: bool | None = None,
                          page: int | None = 1,
                          per_page: int | None = 10) -> list | dict:
        self._validate_params(params=Params, data={'model_class': model_class,
                                                   'filter_type': filter_type,
                                                   'comparison': comparison,
                                                   'column': column,
                                                   'column_value': column_value})
        query: sqlalchemy.orm.Query = self.session.query(model_class)
        model_attr = getattr(model_class, column, None)
        if filter_type == FilterTypes.SEARCH_TEXT:
            self.query_filtered = query.filter(model_attr.ilike(f'%{column_value}%'))
        else:
            comparison_operator = getattr(sqlalchemy.sql.expression.ColumnOperators,
                                          self._comparison.get(comparison)["apply"])
            if column == "creation_date":
                self.query_filtered = query.filter(
                    comparison_operator(model_class.creation_date.cast(sqlalchemy.Date),  # type: ignore
                                        datetime.strptime(column_value, "%Y-%m-%d"))
                )
            # todo: perhaps "else:" is needed here?
            self.query_filtered = query.filter(comparison_operator(model_attr, column_value))
        match paginate:
            case True:
                offset = (page - 1) * per_page
                total: int = self.query_filtered.count()
                model_instances: list[ModelClass] = self.query_filtered.offset(offset).limit(per_page).all()
                paginated_data = {"page": page,
                                  "per_page": per_page,
                                  "total": total,
                                  "total_pages": (total + per_page - 1) // per_page,
                                  "items": [model_instance.get_params() for model_instance in model_instances]}
                return paginated_data
            case _:
                return self.query_filtered.all()


def get_list_or_paginated_data(session,
                               model_class: Type[ModelClass] | None = None,
                               filter_type: FilterTypes | None = None,
                               comparison: Comparison | None = None,
                               column: AdvertisementColumns | UserColumns | None = None,
                               column_value: str | int | datetime | None = None,
                               paginate: bool | None = None,
                               page: int | None = 1,
                               per_page: int | None = 10) -> dict:
    return Filter(session=session).get_filter_result(
        model_class, filter_type, column, column_value, comparison, paginate, page, per_page
    )
