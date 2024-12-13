import enum
import sqlalchemy
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from typing import Type, Literal, Any

from sqlalchemy.orm import Query

from app.models import AdvertisementColumns, UserColumns, ModelClass, User, Advertisement, ModelClasses


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


@dataclass
class QueryBase:
    status: Literal["OK", "Failed"] = "OK"
    errors: set[str] | None = None


@dataclass
class QueryResult(QueryBase):
    query_object: sqlalchemy.orm.Query | None = None


@dataclass
class FilterResult(QueryBase):
    filtered_data: list[ModelClass] | dict[str, int | list[ModelClass]] | None = None


class Filter:

    def __init__(self, session: sqlalchemy.orm.Session, ):
        self.session = session
        self._comparison = {"is": {"apply": "__eq__", "explain": "Equal to"},
                            "is_not": {"apply": "__ne__", "explain": "Not equal to"},
                            "<": {"apply": "__lt__", "explain": "Less than"},
                            "<=": {"apply": "__le__", "explain": "Less than or equal to"},
                            ">": {"apply": "__gt__", "explain": "Greater than"},
                            ">=": {"apply": "__ge__", "explain": "Greater than or equal to"}}
        self.errors: set[str] = set()

    def _add_error(self,
                   param: Params | None = None,
                   invalid_value: Any = None,
                   valid_values: list[Any] | dict[str, Any] | None = None,
                   comment: str | None = None) -> None:
        if not invalid_value and not comment:
            self.errors.add(f"Value for '{param}' is not found.")
        elif comment:
            self.errors.add(comment)
        else:
            self.errors.add(f"'{invalid_value}' is invalid value for '{param}'. Valid values: {valid_values}.")

    def validate_params(self, data: dict[str, Any], params: Type[Params]):
        data_dict = {}
        for param in params:
            data_dict.update({param.value: data.get(param.value)})  # type: ignore
        if data_dict[Params.MODEL_CLASS] not in [mc.value for mc in ModelClasses]:
            self._add_error(Params.MODEL_CLASS, data_dict[Params.MODEL_CLASS], ValidParams.MODEL_CLASS.value)
        if data_dict[Params.FILTER_TYPE] not in ValidParams.FILTER_TYPE.value:
            self._add_error(Params.FILTER_TYPE, data_dict[Params.FILTER_TYPE], ValidParams.FILTER_TYPE.value)
        if data_dict[Params.COLUMN] not in set(ValidParams.COLUMN_USER.value + ValidParams.COLUMN_ADV.value) \
                and data_dict[Params.MODEL_CLASS] not in [mc.value for mc in ModelClasses]:
            self._add_error(
                Params.COLUMN, data_dict[Params.COLUMN], {f"for User": ValidParams.COLUMN_USER.value,
                                                          f"for Advertisement": ValidParams.COLUMN_ADV.value}
            )
        if data_dict[Params.COMPARISON] not in ValidParams.COMPARISON.value:
            self._add_error(Params.COMPARISON, data_dict[Params.COMPARISON], ValidParams.COMPARISON.value)
        match data_dict[Params.COLUMN], data_dict[Params.COLUMN_VALUE]:
            case column, column_value if \
                    column in [UserColumns.ID, AdvertisementColumns.ID, AdvertisementColumns.USER_ID] \
                    and (type(column_value) is not str or not column_value.isdigit()):
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
            case *_, : pass
        match data_dict[Params.FILTER_TYPE], data_dict[Params.COLUMN], data_dict[Params.COMPARISON]:
            case filter_type, column, comparison if filter_type == FilterTypes.COLUMN_VALUE and column in \
                    [UserColumns.NAME, UserColumns.EMAIL, AdvertisementColumns.TITLE, AdvertisementColumns.DESCRIPTION]\
                    and comparison in [Comparison.LE, Comparison.LT, Comparison.GE, Comparison.GT]:
                self._add_error(Params.COMPARISON, comparison, [Comparison.IS.value, Comparison.NOT.value])
            case *_, : pass
        match data_dict[Params.COLUMN], data_dict[Params.MODEL_CLASS]:
            case column, model_class if model_class == User and column not in ValidParams.COLUMN_USER.value:
                self._add_error(Params.COLUMN, column, ValidParams.COLUMN_USER.value)
            case column, model_class if model_class == Advertisement and column not in ValidParams.COLUMN_ADV.value:
                self._add_error(Params.COLUMN, column, ValidParams.COLUMN_ADV.value)
            case *_, : pass

    def _query_object(self,
                      model_class: Type[User | Advertisement],
                      filter_type: FilterTypes,
                      column: AdvertisementColumns | UserColumns,
                      column_value: str,
                      comparison: Comparison | None = None) -> QueryResult:
        if self.errors:
            return QueryResult(status="Failed", errors=self.errors)
        else:
            query_object: sqlalchemy.orm.Query = self.session.query(model_class)
            model_attr = getattr(model_class, column, None)
            comparison_operator = getattr(sqlalchemy.sql.expression.ColumnOperators,
                                          self._comparison[comparison]["apply"])
            match filter_type, column:
                case FilterTypes.COLUMN_VALUE, "creation_date":
                    filtered_query_object = query_object.filter(
                        comparison_operator(model_class.creation_date.cast(sqlalchemy.Date),  # type: ignore
                                            datetime.strptime(column_value, "%Y-%m-%d"))
                    )
                    return QueryResult(query_object=filtered_query_object)
                case FilterTypes.COLUMN_VALUE, _:
                    return QueryResult(query_object=query_object.filter(comparison_operator(model_attr, column_value)))
                case FilterTypes.SEARCH_TEXT, _:
                    return QueryResult(query_object=query_object.filter(model_attr.ilike(f'%{column_value}%')))
                case *_,:
                    return QueryResult()

    def get_list(self,
                 model_class: Type[ModelClass],
                 filter_type: FilterTypes,
                 comparison: Comparison,
                 column: AdvertisementColumns | UserColumns,
                 column_value: str | int | datetime) -> FilterResult:
        query_result: QueryResult = self._query_object(model_class=model_class,
                                                       filter_type=filter_type,
                                                       comparison=comparison,
                                                       column=column,
                                                       column_value=column_value)
        if query_result.status == "OK":
            filter_result: FilterResult = FilterResult(filtered_data=query_result.query_object.all())
        else:
            filter_result: FilterResult = FilterResult(status="Failed", errors=query_result.errors)
        return filter_result

    def paginate(self,
                 model_class: Type[ModelClass],
                 filter_type: FilterTypes,
                 comparison: Comparison,
                 column: AdvertisementColumns | UserColumns,
                 column_value: str | int | datetime,
                 page: int | None = 1,
                 per_page: int | None = 10) -> FilterResult:
        offset = (page - 1) * per_page
        query_result = self._query_object(model_class=model_class,
                                          filter_type=filter_type,
                                          comparison=comparison,
                                          column=column,
                                          column_value=column_value)
        if query_result.status == "OK":
            model_instances: list[ModelClass] = query_result.query_object.offset(offset).limit(per_page).all()
            paginated_data = {"page": page,
                              "per_page": per_page,
                              "total": len(model_instances),
                              "total_pages": (len(model_instances) + per_page - 1) // per_page,
                              "items": [model_instance for model_instance in model_instances]}
            filter_result: FilterResult = FilterResult(filtered_data=paginated_data)
        else:
            filter_result: FilterResult = FilterResult(status="Failed", errors=query_result.errors)
        return filter_result


def filter_and_return_list(session: sqlalchemy.orm.Session,
                           model_class: Type[ModelClass],
                           filter_type: FilterTypes,
                           comparison: Comparison,
                           column: AdvertisementColumns | UserColumns,
                           column_value: str | int | datetime) -> FilterResult:
    filter_result: FilterResult = Filter(session=session).get_list(model_class=model_class,
                                                                   filter_type=filter_type,
                                                                   comparison=comparison,
                                                                   column=column,
                                                                   column_value=column_value)
    return filter_result


def filter_and_return_paginated_data(session: sqlalchemy.orm.Session,
                                     model_class: Type[ModelClass],
                                     filter_type: FilterTypes,
                                     column: AdvertisementColumns | UserColumns,
                                     column_value: str | int | datetime,
                                     comparison: Comparison = Comparison.IS,
                                     page: int | None = 1,
                                     per_page: int | None = 10) -> FilterResult:
    filter_result: FilterResult = Filter(session=session).paginate(model_class=model_class,
                                                                   filter_type=filter_type,
                                                                   comparison=comparison,
                                                                   column=column,
                                                                   column_value=column_value,
                                                                   page=page,
                                                                   per_page=per_page)
    return filter_result
