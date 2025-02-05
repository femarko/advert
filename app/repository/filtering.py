import dataclasses
import enum
import typing

import sqlalchemy
from dataclasses import dataclass
from datetime import datetime
from typing import Type, Literal, Any, Optional

from sqlalchemy.orm import Query

import app.errors
from app import services
from app.models import AdvertisementColumns, UserColumns, ModelClass, User, Advertisement, ModelClasses


class InvalidFilterParams(Exception):
    pass


class FilterTypes(str, enum.Enum):
    COLUMN_VALUE = 'column_value'
    SEARCH_TEXT = 'search_text'


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


class ErrType(str, enum.Enum):
    MISSING = "missing_params"
    INVALID = "invalid_params"


@dataclass
class ParamsValidation:
    missing_params: list[str | Type[Params]]
    invalid_params: dict[str, str | Type[Params]]
    logs: set
    valid_params: dict = dataclasses.field(default_factory=dict)
    params_passed: Optional[dict] = None
    info_types: tuple[ErrType] = (ErrType.MISSING, ErrType.INVALID)

    def create_message(self) -> dict[str, list[str]]:
        result_dict = dict()
        for log in self.logs:
            result_dict |= {"params_passed": self.params_passed, log: getattr(self, log)}
        self.logs = set()
        return result_dict

    def add_error_info(self, info_type: ErrType, info: str | dict):
        attr = getattr(self, info_type)
        match info_type:
            case ErrType.MISSING as it:
                attr.append(info)
                self.logs.add(it)
            case ErrType.INVALID as it:
                attr |= info
                self.logs.add(it)


class Filter:

    def __init__(self, session: sqlalchemy.orm.Session, ):
        self.session = session
        self._comparison = {"is": {"apply": "__eq__", "explain": "Equal to"},
                            "is_not": {"apply": "__ne__", "explain": "Not equal to"},
                            "<": {"apply": "__lt__", "explain": "Less than"},
                            "<=": {"apply": "__le__", "explain": "Less than or equal to"},
                            ">": {"apply": "__gt__", "explain": "Greater than"},
                            ">=": {"apply": "__ge__", "explain": "Greater than or equal to"}}
        self.query_filtered: Optional[Query] = None
        self.res_list: Optional[list] = None
        self.paginated: Optional[dict] = None
        self.page_default_value: int = 1
        self.per_page_default_value: int = 10
        self.params_info = ParamsValidation(
            missing_params=[], invalid_params={}, logs=set(), valid_params={
                'model_class': ValidParams.MODEL_CLASS.value,
                'filter_type': ValidParams.FILTER_TYPE.value,
                'column': list(set(ValidParams.COLUMN_USER.value + ValidParams.COLUMN_ADV.value)),
                ModelClasses.USER.value: ValidParams.COLUMN_USER.value,
                ModelClasses.ADV.value: ValidParams.COLUMN_ADV.value,
                'comparison': ValidParams.COMPARISON.value
            }
        )

    def _validate_params(self, data: dict[str, Any], params: Type[Params]) -> None:
        self.params_info.params_passed = data
        params_dict = {}
        for param in params:
            if param not in self.params_info.params_passed.keys():
                if not(
                        param == Params.COMPARISON and
                        self.params_info.params_passed.get(Params.FILTER_TYPE) == FilterTypes.SEARCH_TEXT
                ):
                    self.params_info.add_error_info(
                        info_type=ErrType.MISSING.value, info=f'{param.value}'  # type: ignore
                    )
            params_dict |= {param.value: data.get(param.value)}  # type: ignore
        for param_name, param_value in params_dict.items():
            if param_value is not None and param_name != Params.COLUMN_VALUE and not (
              param_name == Params.COMPARISON and params_dict.get(Params.FILTER_TYPE.value) == FilterTypes.SEARCH_TEXT
            ):
                if param_value not in self.params_info.valid_params.get(param_name):
                    self.params_info.add_error_info(
                        info_type=ErrType.INVALID.value,
                        info={
                            param_name: f'Valid values are: {self.params_info.valid_params[param_name]}'
                        }
                    )
        match params_dict:
            case {Params.COLUMN.value: c, Params.COLUMN_VALUE.value: cv, Params.FILTER_TYPE.value: ft} if \
              ft == FilterTypes.COLUMN_VALUE and \
              c in [UserColumns.ID, AdvertisementColumns.ID, AdvertisementColumns.USER_ID] and \
              (isinstance(cv, str) and not cv.isdigit() and not isinstance(cv, int)):
                self.params_info.add_error_info(
                    info_type=ErrType.INVALID.value,
                    info={Params.COLUMN_VALUE.value: f'When "{Params.COLUMN.value}" is "{c}", '
                                                     f'"{Params.COLUMN_VALUE.value}" must be a digit.'}
                )
            case {Params.COLUMN.value: c, Params.COLUMN_VALUE.value: cv, Params.FILTER_TYPE: ft} if \
                    c in [UserColumns.CREATION_DATE, AdvertisementColumns.CREATION_DATE] and \
                    ft == FilterTypes.COLUMN_VALUE:
                try:
                    datetime.strptime(cv, "%Y-%m-%d")
                except (ValueError, TypeError):
                    self.params_info.add_error_info(
                        info_type=ErrType.INVALID.value,
                        info={
                            Params.COLUMN_VALUE.value: f'When "{Params.COLUMN.value}" is "{c}", '
                                                       f'"{Params.COLUMN_VALUE.value}" must be a date string of the '
                                                       f'following format: "YYYY-MM-DD".'
                        }
                    )
            case {Params.FILTER_TYPE: Params.COLUMN_VALUE, Params.COLUMN: c, Params.COMPARISON: cmp} if \
                    cmp in [Comparison.LE, Comparison.LT, Comparison.GE, Comparison.GT] and c in \
                    [UserColumns.NAME, UserColumns.EMAIL, AdvertisementColumns.TITLE, AdvertisementColumns.DESCRIPTION]:
                self.params_info.add_error_info(
                    info_type=ErrType.INVALID.value,
                    info={Params.COMPARISON.value: f'When "{Params.FILTER_TYPE.value}" is "{Params.COLUMN_VALUE.value}",'
                                                   f' valid values for "{Params.COMPARISON.value}" are: '
                                                   f'{[Comparison.IS.value, Comparison.NOT.value]}'}
                )
            case {Params.FILTER_TYPE: FilterTypes.SEARCH_TEXT, Params.COLUMN: c, Params.MODEL_CLASS: mc} if c not in \
                    [UserColumns.NAME, UserColumns.EMAIL, AdvertisementColumns.TITLE, AdvertisementColumns.DESCRIPTION]:
                available_columns = []
                match mc:
                    case ModelClasses.USER.value: available_columns = [UserColumns.NAME.value, UserColumns.EMAIL.value]
                    case ModelClasses.ADV.value: available_columns = [
                        AdvertisementColumns.TITLE.value, AdvertisementColumns.DESCRIPTION.value
                    ]
                self.params_info.add_error_info(
                    info_type=ErrType.INVALID.value,
                    info={Params.COLUMN.value: f'For model class "{mc}" text search is available '
                                               f'in the following columns: {available_columns}.'}
                )
            case {Params.MODEL_CLASS.value: mc, Params.COLUMN: c} if \
                    mc == ModelClasses.USER.value and c not in ValidParams.COLUMN_USER.value or \
                    mc == ModelClasses.ADV.value and c not in ValidParams.COLUMN_ADV.value:
                self.params_info.add_error_info(
                    info_type=ErrType.INVALID.value,
                    info={Params.COLUMN.value: f'For model class "{mc}" valid values for "{Params.COLUMN.value}" are: '
                                               f'{self.params_info.valid_params[mc]}.'}
                )
        if self.params_info.logs:
            raise app.errors.ValidationError(message=self.params_info.create_message())

    def _check_page_and_per_page(self, page: Any, per_page: Any) -> dict[Literal["page", "per_page"], int]:
        params_dict = {"page": page, "per_page": per_page}
        for key, value in params_dict.items():
            match value:
                case value if (isinstance(value, int) or (isinstance(value, str) and value.isdigit())) and \
                              int(value) > self.query_filtered.count():
                    if key == "page": params_dict[key] = self.page_default_value
                    else: params_dict[key] = int(value)
                case value if (isinstance(value, int) or (isinstance(value, str) and value.isdigit())) and \
                              0 < int(value) <= self.query_filtered.count():
                    params_dict[key] = int(value)
                case _:
                    if key == "page": params_dict[key] = self.page_default_value
                    else: params_dict[key] = self.per_page_default_value
        return params_dict

    def get_filter_result(self,
                          model_class: Optional[Type[User | Advertisement]] = None,
                          filter_type: Optional[FilterTypes] = None,
                          column: Optional[AdvertisementColumns | UserColumns] = None,
                          column_value: Optional[str] = None,
                          comparison: Optional[Comparison] = None,
                          paginate: Optional[bool] = None,
                          page: Optional[int] = None,
                          per_page: Optional[int] = None) -> list | dict[str, int | list[dict[str, str | int]]]:
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
            self.query_filtered = query.filter(comparison_operator(model_attr, column_value))
        if paginate:
            page_and_per_page = self._check_page_and_per_page(page=page, per_page=per_page)
            page, per_page = page_and_per_page["page"], page_and_per_page["per_page"]
            offset = (page - 1) * per_page
            total: int = self.query_filtered.count()
            model_instances: list[ModelClass] = self.query_filtered.offset(offset).limit(per_page).all()
            paginated_data: dict[str, int | list[dict[str, str | int]]] = {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
                "items": [services.get_params(model=model_instance) for model_instance in model_instances]
            }
            return paginated_data  # type: dict[str, int | list[dict[str, str | int]]]
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
