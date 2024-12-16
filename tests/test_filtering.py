from typing import Any
from datetime import datetime

import pytest
import sqlalchemy.orm

import app.filtering
from app import models, service_layer
from app.error_handlers import HttpError
from app.filtering import Filter, ValidParams, Params


@pytest.mark.parametrize("correct_params,expected_error_message", (({"model_class": models.User,
                                                                     "filter_type": "column_value",
                                                                     "comparison": ">=",
                                                                     "column": "id",
                                                                     "column_value": "1000"}, set()),
                                                                   ({"model_class": models.Advertisement,
                                                                     "filter_type": "column_value",
                                                                     "comparison": ">=",
                                                                     "column": "id",
                                                                     "column_value": "1000"}, set())))
def test_filter_validate_params_with_correct_params(correct_params, expected_error_message):
    fake_session = ...
    filter_object = app.filtering.Filter(session=fake_session)
    filter_object.validate_params(data=correct_params, params=app.filtering.Params)
    assert filter_object.errors == expected_error_message


@pytest.mark.parametrize(
    "wrong_params,expected_error_message",
    (
            # ({"model_class": "wrong_param",
            #   "filter_type": "wrong_param",
            #   "comparison": "wrong_param",
            #   "column": "wrong_param",
            #   "column_value": "wrong_param"}, {
            #      f"'wrong_param' is invalid value for 'model_class'. Valid values: "
            #      f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
            #      f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
            #      f"'wrong_param' is invalid value for 'comparison'. "
            #      f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
            #      f'\'wrong_param\' is invalid value for \'column\'. Valid values: '
            #      f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
            #      f'"for <class \'app.models.Advertisement\'>": '
            #      f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'
            # },),
            # ({}, {f"Value for 'model_class' is not found.",
            #       f"Value for 'filter_type' is not found.",
            #       f"Value for 'comparison' is not found.",
            #       f"Value for 'column' is not found."}),
            ({"model_class": "",
              "filter_type": "",
              "comparison": "",
              "column": "",
              "column_value": ""}, {
                f"'' is invalid value for 'model_class'. Valid values: "
                f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
                f"'' is invalid value for 'filter_type'. "
                f"Valid values: ['column_value', 'search_text'].",
                f"'' is invalid value for 'comparison'. "
                f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
                f'\'\' is invalid value for \'column\'. Valid values: '
                f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
                f'"for <class \'app.models.Advertisement\'>": '
                f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'}),
            # ({"model_class": "wrong_param",
            #   "filter_type": "column_value",
            #   "comparison": "is",
            #   "column": "name",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'model_class'. "
            #                                         f"Valid values: "
            #                                         f"[<class 'app.models.User'>, "
            #                                         f"<class 'app.models.Advertisement'>]."}),
            # ({"model_class": models.Advertisement,
            #   "filter_type": "wrong_param",
            #   "comparison": "is",
            #   "column": "title",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'filter_type'. "
            #                                         f"Valid values: ['column_value', 'search_text']."}),
            # ({"model_class": models.User,
            #   "filter_type": "column_value",
            #   "comparison": "wrong_param",
            #   "column": "name",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'comparison'. "
            #                                         f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            # ({"model_class": models.Advertisement,
            #   "filter_type": "column_value",
            #   "comparison": "wrong_param",
            #   "column": "name",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'comparison'. "
            #                                         f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
            #                                         f"'name' is invalid value for 'column'. "
            #                                         f"Valid values: "
            #                                         f"['id', 'title', 'description', 'creation_date', 'user_id']."}),
            # ({"model_class": models.User,
            #   "filter_type": "column_value",
            #   "comparison": "is",
            #   "column": "wrong_param",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'column'. "
            #                                         f"Valid values: ['id', 'name', 'email', 'creation_date']."}),
            # ({"model_class": models.Advertisement,
            #   "filter_type": "column_value",
            #   "comparison": "is",
            #   "column": "wrong_param",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'column'. "
            #                                         f"Valid values: "
            #                                         f"['id', 'title', 'description', 'creation_date', 'user_id']."}),
            # ({"model_class": models.User,
            #   "filter_type": "column_value",
            #   "comparison": "is",
            #   "column": "name",
            #   "column_value": "wrong_param"}, set()),
            # ({"model_class": "wrong_param",
            #   "filter_type": "wrong_param",
            #   "comparison": "is",
            #   "column": "name",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'model_class'. "
            #                                         f"Valid values: "
            #                                         f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
            #                                         f"'wrong_param' is invalid value for 'filter_type'. "
            #                                         f"Valid values: ['column_value', 'search_text']."}),
            # ({"model_class": "wrong_param",
            #   "filter_type": "column_value",
            #   "comparison": "wrong_param",
            #   "column": "name",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'model_class'. "
            #                                         f"Valid values: "
            #                                         f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
            #                                         f"'wrong_param' is invalid value for 'comparison'. "
            #                                         f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            # ({"model_class": "wrong_param",
            #   "filter_type": "column_value",
            #   "comparison": "is",
            #   "column": "wrong_param",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'model_class'. "
            #                                         f"Valid values: "
            #                                         f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
            #                                         f"'wrong_param' is invalid value for 'column'. "
            #                                         f"Valid values: "
            #                                         f"{{'for User': ['id', 'name', 'email', 'creation_date'], "
            #                                         f"'for Advertisement': "
            #                                         f"['id', 'title', 'description', 'creation_date', 'user_id']}}."}),
            # ({"model_class": "wrong_param",
            #   "filter_type": "column_value",
            #   "comparison": "is",
            #   "column": "name",
            #   "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'model_class'. "
            #                                    f"Valid values: "
            #                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>]."}),
            # ({"model_class": models.User,
            #   "filter_type": "wrong_param",
            #   "comparison": "wrong_param",
            #   "column": "name",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'filter_type'. "
            #                                         f"Valid values: ['column_value', 'search_text'].",
            #                                         f"'wrong_param' is invalid value for 'comparison'. "
            #                                         f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            # ({"model_class": models.User,
            #   "filter_type": "wrong_param",
            #   "comparison": "is",
            #   "column": "wrong_param",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'filter_type'. "
            #                                         f"Valid values: ['column_value', 'search_text'].",
            #                                         f"'wrong_param' is invalid value for 'column'. "
            #                                         f"Valid values: ['id', 'name', 'email', 'creation_date']."}),
            # ({"model_class": models.User,
            #   "filter_type": "wrong_param",
            #   "comparison": "is",
            #   "column": "name",
            #   "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'filter_type'. "
            #                                    f"Valid values: ['column_value', 'search_text']."}),
            # ({"model_class": models.User,
            #   "filter_type": "column_value",
            #   "comparison": "wrong_param",
            #   "column": "wrong_param",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'comparison'. "
            #                                         f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
            #                                         f"'wrong_param' is invalid value for 'column'. "
            #                                         f"Valid values: ['id', 'name', 'email', 'creation_date']."}),
            # ({"model_class": models.User,
            #   "filter_type": "column_value",
            #   "comparison": "wrong_param",
            #   "column": "name",
            #   "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'comparison'. "
            #                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            # ({"model_class": models.User,
            #   "filter_type": "column_value",
            #   "comparison": "is",
            #   "column": "wrong_param",
            #   "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'column'. "
            #                                    f"Valid values: ['id', 'name', 'email', 'creation_date']."}),
            # ({"model_class": "wrong_param",
            #   "filter_type": "wrong_param",
            #   "comparison": "wrong_param",
            #   "column": "name",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'model_class'. "
            #                                         f"Valid values: "
            #                                         f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
            #                                         f"'wrong_param' is invalid value for 'filter_type'. "
            #                                         f"Valid values: ['column_value', 'search_text'].",
            #                                         f"'wrong_param' is invalid value for 'comparison'. "
            #                                         f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            # ({"model_class": "wrong_param",
            #   "filter_type": "wrong_param",
            #   "comparison": "is",
            #   "column": "wrong_param",
            #   "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'model_class'. "
            #                                         f"Valid values: "
            #                                         f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
            #                                         f"'wrong_param' is invalid value for 'filter_type'. "
            #                                         f"Valid values: ['column_value', 'search_text'].",
            #                                         f"'wrong_param' is invalid value for 'column'. "
            #                                         f"Valid values: "
            #                                         f"{{'for User': ['id', 'name', 'email', 'creation_date'], "
            #                                         f"'for Advertisement': "
            #                                         f"['id', 'title', 'description', 'creation_date', 'user_id']}}."}),
            # ({"model_class": "wrong_param",
            #   "filter_type": "wrong_param",
            #   "comparison": "is",
            #   "column": "name",
            #   "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'model_class'. "
            #                                    f"Valid values: "
            #                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
            #                                    f"'wrong_param' is invalid value for 'filter_type'. "
            #                                    f"Valid values: ['column_value', 'search_text']."}),
            # ({"model_class": "wrong_param",
            #   "filter_type": "column_value",
            #   "comparison": "wrong_param",
            #   "column": "name",
            #   "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'model_class'. "
            #                                    f"Valid values: "
            #                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
            #                                    f"'wrong_param' is invalid value for 'comparison'. "
            #                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            # ({"model_class": "wrong_param",
            #   "filter_type": "column_value",
            #   "comparison": "is",
            #   "column": "wrong_param",
            #   "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'model_class'. "
            #                                    f"Valid values: "
            #                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
            #                                    f"'wrong_param' is invalid value for 'column'. "
            #                                    f"Valid values: {{'for User': ['id', 'name', 'email', 'creation_date'], "
            #                                    f"'for Advertisement': "
            #                                    f"['id', 'title', 'description', 'creation_date', 'user_id']}}."}),
            # ({"model_class": models.User,
            #   "filter_type": "wrong_param",
            #   "comparison": "wrong_param",
            #   "column": "name",
            #   "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'filter_type'. "
            #                                    f"Valid values: ['column_value', 'search_text'].",
            #                                    f"'wrong_param' is invalid value for 'comparison'. "
            #                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            # ({"model_class": models.User,
            #   "filter_type": "wrong_param",
            #   "comparison": "is",
            #   "column": "wrong_param",
            #   "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'filter_type'. "
            #                                    f"Valid values: ['column_value', 'search_text'].",
            #                                    f"'wrong_param' is invalid value for 'column'. "
            #                                    f"Valid values: ['id', 'name', 'email', 'creation_date']."}),
            # ({"model_class": models.User,
            #   "filter_type": "column_value",
            #   "comparison": "wrong_param",
            #   "column": "wrong_param",
            #   "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'comparison'. "
            #                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
            #                                    f"'wrong_param' is invalid value for 'column'. "
            #                                    f"Valid values: ['id', 'name', 'email', 'creation_date']."}),
            # ({"model_class": models.User,
            #   "filter_type": "column_value",
            #   "comparison": "is",
            #   "column": "id",
            #   "column_value": "wrong_param"}, {f"'id' must be a digit."}),
            # ({"model_class": models.User,
            #   "filter_type": "column_value",
            #   "comparison": "is",
            #   "column": "creation_date",
            #   "column_value": "some_string"}, {f"When column='creation_date', 'column_value' must be a date "
            #                                    f"string of the following format: 'YYYY-MM-DD'."}),
            # ({"model_class": models.User,
            #   "filter_type": "column_value",
            #   "comparison": "is",
            #   "column": "creation_date",
            #   "column_value": 2024}, {f"When column='creation_date', 'column_value' must be a date "
            #                           f"string of the following format: 'YYYY-MM-DD'."}),
            # ({"model_class": models.User,
            #   "filter_type": "column_value",
            #   "comparison": ">",
            #   "column": "name",
            #   "column_value": "test_filter_1000"}, {f"'>' is invalid value for 'comparison'. "
            #                                         f"Valid values: ['is', 'is_not']."}),
            # ({"model_class": models.User,
            #   "filter_type": "search_text",
            #   "comparison": "",
            #   "column": "id",
            #   "column_value": "1000"}, {"For filter_type='search_text' the folowing columns are available: "
            #                             "{for '<class 'app.models.User'>': [name, email], "
            #                             "for '<class 'app.models.Advertisement'>': [title, description]}"})
    )
)
def test_filter_validate_params_with_wrong_params(wrong_params, expected_error_message):
    fake_session = ...
    filter_object = app.filtering.Filter(session=fake_session)
    filter_object.validate_params(data=wrong_params, params=app.filtering.Params)
    assert filter_object.errors == expected_error_message


@pytest.mark.parametrize("params", (  # {"model_class": models.User,
        # "filter_type": "column_value",
        # "comparison": ">=",
        # "column": "id",
        # "column_value": "1000"},
        {"model_class": models.User,
         "filter_type": "search_text",
         "comparison": "",
         "column": "id",
         "column_value": "1000"},
        # {"model_class": models.Advertisement,
        #  "filter_type": "column_value",
        #  "comparison": ">=",
        #  "column": "id",
        #  "column_value": "1000"},
))
def test__query_object_with_correct_params(session_maker, create_test_users_and_advs, params):
    session = session_maker
    with session() as sess:
        query_result = app.filtering.Filter(session=sess)._query_object(**params)
    assert query_result.status == "OK"
    assert type(query_result.query_object) == sqlalchemy.orm.Query
    for item in query_result.query_object.all():
        assert isinstance(item, params["model_class"])
    assert query_result.query_object.all()[0].id == 1000
    assert query_result.query_object.all()[1].id == 1001
    assert query_result.errors is None


@pytest.mark.parametrize(
    "wrong_params,expected_error_message",
    (
            ({"model_class": "wrong_param",
              "filter_type": "wrong_param",
              "comparison": "wrong_param",
              "column": "wrong_param",
              "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'model_class'. "
                                               f"Valid values: "
                                               f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
                                               f"'wrong_param' is invalid value for 'filter_type'. "
                                               f"Valid values: ['column_value', 'search_text'].",
                                               f"'wrong_param' is invalid value for 'comparison'. "
                                               f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
                                               f"'wrong_param' is invalid value for 'column'. Valid values: "
                                               f"{{'for User': ['id', 'name', 'email', 'creation_date'], "
                                               f"'for Advertisement': "
                                               f"['id', 'title', 'description', 'creation_date', 'user_id']}}."}),
            ({}, {f"Value for 'model_class' is not found.",
                  f"Value for 'filter_type' is not found.",
                  f"Value for 'comparison' is not found.",
                  f"Value for 'column' is not found."}),
            ({"model_class": "wrong_param",
              "filter_type": "column_value",
              "comparison": "is",
              "column": "name",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'model_class'. "
                                                    f"Valid values: "
                                                    f"[<class 'app.models.User'>, "
                                                    f"<class 'app.models.Advertisement'>]."}),
            ({"model_class": models.Advertisement,
              "filter_type": "wrong_param",
              "comparison": "is",
              "column": "title",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'filter_type'. "
                                                    f"Valid values: ['column_value', 'search_text']."}),
            ({"model_class": models.User,
              "filter_type": "column_value",
              "comparison": "wrong_param",
              "column": "name",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'comparison'. "
                                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            ({"model_class": models.Advertisement,
              "filter_type": "column_value",
              "comparison": "wrong_param",
              "column": "name",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'comparison'. "
                                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
                                                    f"'name' is invalid value for 'column'. "
                                                    f"Valid values: "
                                                    f"['id', 'title', 'description', 'creation_date', 'user_id']."}),
            ({"model_class": models.User,
              "filter_type": "column_value",
              "comparison": "is",
              "column": "wrong_param",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'column'. "
                                                    f"Valid values: ['id', 'name', 'email', 'creation_date']."}),
            ({"model_class": models.Advertisement,
              "filter_type": "column_value",
              "comparison": "is",
              "column": "wrong_param",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'column'. "
                                                    f"Valid values: "
                                                    f"['id', 'title', 'description', 'creation_date', 'user_id']."}),
            ({"model_class": models.User,
              "filter_type": "column_value",
              "comparison": "is",
              "column": "name",
              "column_value": "wrong_param"}, None),
            ({"model_class": "wrong_param",
              "filter_type": "wrong_param",
              "comparison": "is",
              "column": "name",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'model_class'. "
                                                    f"Valid values: "
                                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
                                                    f"'wrong_param' is invalid value for 'filter_type'. "
                                                    f"Valid values: ['column_value', 'search_text']."}),
            ({"model_class": "wrong_param",
              "filter_type": "column_value",
              "comparison": "wrong_param",
              "column": "name",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'model_class'. "
                                                    f"Valid values: "
                                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
                                                    f"'wrong_param' is invalid value for 'comparison'. "
                                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            ({"model_class": "wrong_param",
              "filter_type": "column_value",
              "comparison": "is",
              "column": "wrong_param",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'model_class'. "
                                                    f"Valid values: "
                                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
                                                    f"'wrong_param' is invalid value for 'column'. "
                                                    f"Valid values: "
                                                    f"{{'for User': ['id', 'name', 'email', 'creation_date'], "
                                                    f"'for Advertisement': "
                                                    f"['id', 'title', 'description', 'creation_date', 'user_id']}}."}),
            ({"model_class": "wrong_param",
              "filter_type": "column_value",
              "comparison": "is",
              "column": "name",
              "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'model_class'. "
                                               f"Valid values: "
                                               f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>]."}),
            ({"model_class": models.User,
              "filter_type": "wrong_param",
              "comparison": "wrong_param",
              "column": "name",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'filter_type'. "
                                                    f"Valid values: ['column_value', 'search_text'].",
                                                    f"'wrong_param' is invalid value for 'comparison'. "
                                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            ({"model_class": models.User,
              "filter_type": "wrong_param",
              "comparison": "is",
              "column": "wrong_param",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'filter_type'. "
                                                    f"Valid values: ['column_value', 'search_text'].",
                                                    f"'wrong_param' is invalid value for 'column'. "
                                                    f"Valid values: ['id', 'name', 'email', 'creation_date']."}),
            ({"model_class": models.User,
              "filter_type": "wrong_param",
              "comparison": "is",
              "column": "name",
              "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'filter_type'. "
                                               f"Valid values: ['column_value', 'search_text']."}),
            ({"model_class": models.User,
              "filter_type": "column_value",
              "comparison": "wrong_param",
              "column": "wrong_param",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'comparison'. "
                                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
                                                    f"'wrong_param' is invalid value for 'column'. "
                                                    f"Valid values: ['id', 'name', 'email', 'creation_date']."}),
            ({"model_class": models.User,
              "filter_type": "column_value",
              "comparison": "wrong_param",
              "column": "name",
              "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'comparison'. "
                                               f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            ({"model_class": models.User,
              "filter_type": "column_value",
              "comparison": "is",
              "column": "wrong_param",
              "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'column'. "
                                               f"Valid values: ['id', 'name', 'email', 'creation_date']."}),
            ({"model_class": "wrong_param",
              "filter_type": "wrong_param",
              "comparison": "wrong_param",
              "column": "name",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'model_class'. "
                                                    f"Valid values: "
                                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
                                                    f"'wrong_param' is invalid value for 'filter_type'. "
                                                    f"Valid values: ['column_value', 'search_text'].",
                                                    f"'wrong_param' is invalid value for 'comparison'. "
                                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            ({"model_class": "wrong_param",
              "filter_type": "wrong_param",
              "comparison": "is",
              "column": "wrong_param",
              "column_value": "test_filter_1000"}, {f"'wrong_param' is invalid value for 'model_class'. "
                                                    f"Valid values: "
                                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
                                                    f"'wrong_param' is invalid value for 'filter_type'. "
                                                    f"Valid values: ['column_value', 'search_text'].",
                                                    f"'wrong_param' is invalid value for 'column'. "
                                                    f"Valid values: "
                                                    f"{{'for User': ['id', 'name', 'email', 'creation_date'], "
                                                    f"'for Advertisement': "
                                                    f"['id', 'title', 'description', 'creation_date', 'user_id']}}."}),
            ({"model_class": "wrong_param",
              "filter_type": "wrong_param",
              "comparison": "is",
              "column": "name",
              "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'model_class'. "
                                               f"Valid values: "
                                               f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
                                               f"'wrong_param' is invalid value for 'filter_type'. "
                                               f"Valid values: ['column_value', 'search_text']."}),
            ({"model_class": "wrong_param",
              "filter_type": "column_value",
              "comparison": "wrong_param",
              "column": "name",
              "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'model_class'. "
                                               f"Valid values: "
                                               f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
                                               f"'wrong_param' is invalid value for 'comparison'. "
                                               f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            ({"model_class": "wrong_param",
              "filter_type": "column_value",
              "comparison": "is",
              "column": "wrong_param",
              "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'model_class'. "
                                               f"Valid values: "
                                               f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
                                               f"'wrong_param' is invalid value for 'column'. "
                                               f"Valid values: {{'for User': ['id', 'name', 'email', 'creation_date'], "
                                               f"'for Advertisement': "
                                               f"['id', 'title', 'description', 'creation_date', 'user_id']}}."}),
            ({"model_class": models.User,
              "filter_type": "wrong_param",
              "comparison": "wrong_param",
              "column": "name",
              "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'filter_type'. "
                                               f"Valid values: ['column_value', 'search_text'].",
                                               f"'wrong_param' is invalid value for 'comparison'. "
                                               f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}),
            ({"model_class": models.User,
              "filter_type": "wrong_param",
              "comparison": "is",
              "column": "wrong_param",
              "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'filter_type'. "
                                               f"Valid values: ['column_value', 'search_text'].",
                                               f"'wrong_param' is invalid value for 'column'. "
                                               f"Valid values: ['id', 'name', 'email', 'creation_date']."}),
            ({"model_class": models.User,
              "filter_type": "column_value",
              "comparison": "wrong_param",
              "column": "wrong_param",
              "column_value": "wrong_param"}, {f"'wrong_param' is invalid value for 'comparison'. "
                                               f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
                                               f"'wrong_param' is invalid value for 'column'. "
                                               f"Valid values: ['id', 'name', 'email', 'creation_date']."}),
            ({"model_class": models.User,
              "filter_type": "column_value",
              "comparison": "is",
              "column": "id",
              "column_value": "wrong_param"}, {f"'id' must be a digit."}),
            ({"model_class": models.User,
              "filter_type": "column_value",
              "comparison": "is",
              "column": "creation_date",
              "column_value": "some_string"}, {f"When column='creation_date', 'column_value' must be a date "
                                               f"string of the following format: 'YYYY-MM-DD'."}),
            ({"model_class": models.User,
              "filter_type": "column_value",
              "comparison": "is",
              "column": "creation_date",
              "column_value": 2024}, {f"When column='creation_date', 'column_value' must be a date "
                                      f"string of the following format: 'YYYY-MM-DD'."}),
            ({"model_class": models.User,
              "filter_type": "column_value",
              "comparison": ">",
              "column": "name",
              "column_value": "test_filter_1000"}, {f"'>' is invalid value for 'comparison'. "
                                                    f"Valid values: ['is', 'is_not']."}),
    )
)
def test__query_object_with_wrong_params(
        session_maker, wrong_params, expected_error_message
):
    session = session_maker
    with session() as sess:
        query_result = app.filtering.Filter(session=sess)._query_object(**wrong_params)
    assert query_result.errors == expected_error_message


@pytest.mark.parametrize(
    "model_class,filter_type,column,column_value,comparison",
    (
            (models.User, "search_text", "email", "st_f", ""),
            (models.Advertisement, "search_text", "title", "ilt", ""),
            (models.User, "column_value", "id", 1000, ">="),
            (models.User, "column_value", "creation_date", "1900-01-01", "<="),
            (models.Advertisement, "column_value", "creation_date", "1900-01-01", "<="),
            (models.Advertisement, "column_value", "user_id", 1000, ">="),
    )
)
def test_filter_and_return_list_with_correct_params(session_maker, model_class, filter_type, column, column_value,
                                                    comparison, create_test_users_and_advs, test_date):
    session = session_maker
    with session() as sess:
        filter_result = app.filtering.filter_and_return_list(session=sess,
                                                             model_class=model_class,
                                                             filter_type=filter_type,  # type: ignore
                                                             column=column,  # type: ignore
                                                             comparison=comparison,  # type: ignore
                                                             column_value=column_value)
    assert type(filter_result) is app.filtering.FilterResult
    assert filter_result.status == "OK"
    assert type(filter_result.filtered_data) is list
    assert len(filter_result.filtered_data) == 2
    assert isinstance(filter_result.filtered_data[0], model_class) and \
           isinstance(filter_result.filtered_data[1], model_class)
    assert filter_result.filtered_data[0].id == 1000
    assert filter_result.filtered_data[1].id == 1001
    assert filter_result.filtered_data[0].creation_date == filter_result.filtered_data[1].creation_date == test_date


@pytest.mark.parametrize(
    "model_class,filter_type,column,column_value,comparison",
    (
            (models.User, "search_text", "email", "st_f", ""),
            (models.Advertisement, "search_text", "title", "ilt", ""),
            (models.User, "column_value", "id", 1000, ">="),
            (models.User, "column_value", "creation_date", "1900-01-01", "<="),
            (models.Advertisement, "column_value", "creation_date", "1900-01-01", "<="),
            (models.Advertisement, "column_value", "user_id", 1000, ">="),
    )
)
def test_filter_and_return_paginated_data_with_correct_params(
        session_maker, model_class, filter_type, column, column_value, comparison, create_test_users_and_advs, test_date
):
    session = session_maker
    with session() as sess:
        filter_result = app.filtering.filter_and_return_paginated_data(session=sess,
                                                                       model_class=model_class,
                                                                       filter_type=filter_type,  # type: ignore
                                                                       column=column,  # type: ignore
                                                                       comparison=comparison,  # type: ignore
                                                                       column_value=column_value)
    assert type(filter_result) is app.filtering.FilterResult
    assert filter_result.status == "OK"
    assert type(filter_result.filtered_data) is dict
    assert filter_result.filtered_data["page"] == 1
    assert filter_result.filtered_data["per_page"] == 10
    assert filter_result.filtered_data["total"] == 2
    assert filter_result.filtered_data["total_pages"] == 1
    assert type(filter_result.filtered_data["items"]) == list
    assert len(filter_result.filtered_data["items"]) == 2
    assert isinstance(filter_result.filtered_data["items"][0], model_class) and \
           isinstance(filter_result.filtered_data["items"][1], model_class)
    assert filter_result.filtered_data["items"][0].id == 1000 and \
           filter_result.filtered_data["items"][1].id == 1001


def test_filter_and_return_list_with_wrong_filter_type_comparison_and_column_parameters(
        session_maker, create_test_users_and_advs, test_date
):
    session = session_maker
    with session() as sess:
        filter_result = app.filtering.filter_and_return_list(session=sess,
                                                             model_class=models.Advertisement,  # type: ignore
                                                             filter_type="wrong_filter_type",  # type: ignore
                                                             column="wrong_column",  # type: ignore
                                                             comparison="wrong_comparison",  # type: ignore
                                                             column_value="test_filter")  # type: ignore
    assert filter_result.status == "Failed"
    assert filter_result.errors == ["Unexpected or missing 'column' parameter.",
                                    "Unexpected or missing 'filter_type' parameter."]
    assert filter_result.filtered_data is None


def test_filter_and_return_paginated_data_with_wrong_filter_type_comparison_and_column_parameters(
        session_maker, create_test_users_and_advs, test_date
):
    session = session_maker
    with session() as sess:
        filter_result = app.filtering.filter_and_return_list(session=sess,
                                                             model_class=models.Advertisement,  # type: ignore
                                                             filter_type="wrong_filter_type",  # type: ignore
                                                             column="wrong_column",  # type: ignore
                                                             comparison="wrong_comparison",  # type: ignore
                                                             column_value="test_filter")  # type: ignore
    assert filter_result.status == "Failed"
    assert filter_result.errors == ["Unexpected or missing 'column' parameter.",
                                    "Unexpected or missing 'filter_type' parameter."]
    assert filter_result.filtered_data is None


@pytest.mark.parametrize("creation_date_value", ("01.01.1900", "01/01/1900", "1-1-1900"))
def test_filter_and_return_list_with_wrong_creation_data_format_as_column_value_parameter(
        session_maker, create_test_users_and_advs, creation_date_value
):
    session = session_maker
    with session() as sess:
        filter_result = app.filtering.filter_and_return_list(session=sess,
                                                             model_class=models.Advertisement,  # type: ignore
                                                             filter_type="column_value",  # type: ignore
                                                             column="creation_date",  # type: ignore
                                                             comparison="is",  # type: ignore
                                                             column_value=creation_date_value)  # type: ignore
    assert filter_result.status == "Failed"
    assert filter_result.errors == [f"time data '{creation_date_value}' does not match format '%Y-%m-%d'"]
    assert filter_result.filtered_data is None


@pytest.mark.parametrize("creation_date_value", ("01.01.1900", "01/01/1900", "1-1-1900"))
def test_filter_and_return_paginated_data_with_wrong_creation_data_format_as_column_value_parameter(
        session_maker, create_test_users_and_advs, creation_date_value
):
    session = session_maker
    with session() as sess:
        filter_result = app.filtering.filter_and_return_paginated_data(session=sess,
                                                                       model_class=models.Advertisement,  # type: ignore
                                                                       filter_type="column_value",  # type: ignore
                                                                       column="creation_date",  # type: ignore
                                                                       comparison="is",  # type: ignore
                                                                       column_value=creation_date_value)  # type: ignore
    assert filter_result.status == "Failed"
    assert filter_result.errors == [f"time data '{creation_date_value}' does not match format '%Y-%m-%d'"]
    assert filter_result.filtered_data is None


def test_filter_and_return_list_with_wrong_comparison_and_column_parameters(
        session_maker, create_test_users_and_advs, test_date
):
    session = session_maker
    with session() as sess:
        filter_result = app.filtering.filter_and_return_list(session=sess,
                                                             model_class=models.Advertisement,  # type: ignore
                                                             filter_type="column_value",  # type: ignore
                                                             column="wrong_column",  # type: ignore
                                                             comparison="wrong_comparison",  # type: ignore
                                                             column_value="test_filter")  # type: ignore
    assert filter_result.status == "Failed"
    assert filter_result.errors == ["Unexpected or missing 'column' parameter.",
                                    "Unexpected or missing 'comparison' parameter."]
    assert filter_result.filtered_data is None


def test_filter_and_return_paginated_data_with_wrong_comparison_and_column_parameters(
        session_maker, create_test_users_and_advs, test_date
):
    session = session_maker
    with session() as sess:
        filter_result = app.filtering.filter_and_return_paginated_data(session=sess,
                                                                       model_class=models.Advertisement,  # type: ignore
                                                                       filter_type="column_value",  # type: ignore
                                                                       column="wrong_column",  # type: ignore
                                                                       comparison="wrong_comparison",  # type: ignore
                                                                       column_value="test_filter")  # type: ignore
    assert filter_result.status == "Failed"
    assert filter_result.errors == ["Unexpected or missing 'column' parameter.",
                                    "Unexpected or missing 'comparison' parameter."]
    assert filter_result.filtered_data is None


def test_filter_and_return_list_with_wrong_filter_type_parameter(
        session_maker, create_test_users_and_advs, test_date
):
    session = session_maker
    with session() as sess:
        filter_result = app.filtering.filter_and_return_list(session=sess,
                                                             model_class=models.Advertisement,  # type: ignore
                                                             filter_type="wrong_filter_type",  # type: ignore
                                                             column="id",  # type: ignore
                                                             comparison="is",  # type: ignore
                                                             column_value="1000")  # type: ignore
    assert filter_result.status == "Failed"
    assert filter_result.errors == ["Unexpected or missing 'filter_type' parameter."]
    assert filter_result.filtered_data is None


def test_filter_and_return_paginated_data_with_wrong_filter_type_parameter(
        session_maker, create_test_users_and_advs, test_date
):
    session = session_maker
    with session() as sess:
        filter_result = app.filtering.filter_and_return_paginated_data(session=sess,
                                                                       model_class=models.Advertisement,  # type: ignore
                                                                       filter_type="wrong_filter_type",  # type: ignore
                                                                       column="id",  # type: ignore
                                                                       comparison="is",  # type: ignore
                                                                       column_value="1000")  # type: ignore
    assert filter_result.status == "Failed"
    assert filter_result.errors == ["Unexpected or missing 'filter_type' parameter."]
    assert filter_result.filtered_data is None

# @pytest.mark.parametrize(
#     "model_class,comparison,column",
#     (
#             pytest.param(models.User, "is", "", marks=pytest.mark.xfail(raises=AttributeError)),
#             pytest.param(models.User, ">", "", marks=pytest.mark.xfail(raises=AttributeError)),
#             (models.User, "is", "creation_date"),
#             (models.User, "<=", "creation_date"),
#             (models.Advertisement, "is", "creation_date"),
#             (models.Advertisement, "<=", "creation_date"),
#     )
# )
# def test_filter_with_creation_date(
#         session_maker, model_class, comparison, column, create_test_users_and_advs, test_date
# ):
#     session = session_maker
#     with session() as sess:
#         results = app.filtering.filter_and_return_list(session=sess,
#                                                        model_class=model_class,
#                                                        filter_type="column_value",  # type: ignore
#                                                        comparison=comparison,  # type: ignore
#                                                        column=column,  # type: ignore
#                                                        column_value="1900-01-01")
#     assert type(results) is list
#     assert len(results) == 2
#     assert results[0].id == 1000
#     assert results[1].id == 1001
#     assert results[0].creation_date == results[1].creation_date == test_date
#
#
# @pytest.mark.parametrize(
#     "model_class,comparison,column",
#     ((models.User, "is", "name"),
#      (models.Advertisement, "is", "title")),
#
# )
# def test_filter_with_creation_date_and_wrong_column_parameter_returns_empty_list(
#         session_maker, model_class, comparison, column, create_test_users_and_advs_for_filtering, test_date
# ):
#     session = session_maker
#     with session() as sess:
#         results = app.filtering.filter_and_return_list(session=sess,
#                                                        model_class=model_class,
#                                                        filter_type="column_value",  # type: ignore
#                                                        comparison=comparison,  # type: ignore
#                                                        column=column,  # type: ignore
#                                                        column_value="1900-01-01")
#     assert results == []
#
#
# @pytest.mark.run(order=3)
# @pytest.mark.parametrize("model_class,filter_type,column,column_value",
#                          ((models.User, "search_text", "email", "st_1"),
#                           (models.User, "column_value", "email", "test_1@email.com"),
#                           (models.User, "column_value", "id", 1)))
# def test_filter_users_with_paginate_and_correct_data(session_maker, model_class, filter_type, column, column_value, ):
#     session = session_maker
#     with session() as sess:
#         expected = sess.execute(sqlalchemy.text('SELECT * FROM "user" WHERE id = 1')).first()
#     with session() as sess:
#         filter_object = app.filtering.Filter(session=sess)
#     results = filter_object.paginate(model_class=model_class,
#                                      filter_type=filter_type, column=column,  # type: ignore
#                                      column_value=column_value,
#                                      per_page=1)
#     assert type(results) is dict
#     assert results["page"] == 1
#     assert results["per_page"] == 1
#     assert results["total"] == 1
#     assert results["total_pages"] == 1
#     assert type(results["items"]) is list
#     assert results["items"][0].id == expected[0]
#     assert results["items"][0].name == expected[1]
#     assert results["items"][0].email == expected[2]
#     assert results["items"][0].password == expected[3]
#     assert results["items"][0].creation_date == expected[4]
#
#
# @pytest.mark.run(order=4)
# @pytest.mark.parametrize(
#     "model_class,filter_type,column,column_value",
#     (
#             (models.Advertisement, "search_text", "description", "tion_1"),
#             (models.Advertisement, "column_value", "description", "test_description_1"),
#     )
# )
# def test_filter_advs_with_get_list_and_correct_data(session_maker, model_class, filter_type, column, column_value,
#                                                     create_test_date_users):
#     session = session_maker
#     with session() as sess:
#         expected = sess.execute(sqlalchemy.text("SELECT * FROM adv WHERE id = 1")).first()
#     with session() as sess:
#         filter_object = app.filtering.Filter(session=sess)
#     results = filter_object.get_list(model_class=model_class,
#                                      filter_type=filter_type,  # type: ignore
#                                      column=column,  # type: ignore
#                                      column_value=column_value)
#     assert type(results) is list
#     assert results[0].id == expected[0]
#     assert results[0].title == expected[1]
#     assert results[0].description == expected[2]
#     assert results[0].creation_date == expected[3]
#     assert results[0].user_id == expected[4]
#
#
# @pytest.mark.run(order=4)
# @pytest.mark.parametrize(
#     "model_class,filter_type,column,column_value",
#     (
#             (models.Advertisement, "search_text", "description", "tion_1"),
#             (models.Advertisement, "column_value", "description", "test_description_1"),
#     )
# )
# def test_filter_adv_instances_with_correct_data(session_maker, model_class, filter_type, column, column_value):
#     session = session_maker
#     with session() as sess:
#         expected = sess.execute(sqlalchemy.text("SELECT * FROM adv WHERE id = 1")).first()
#     with session() as sess:
#         filter_object = app.filtering.Filter(session=sess)
#     results = filter_object.paginate(model_class=model_class,
#                                      filter_type=filter_type,  # type: ignore
#                                      column=column,  # type: ignore
#                                      column_value=column_value,
#                                      per_page=1)
#     assert type(results) is dict
#     assert results["page"] == 1
#     assert results["per_page"] == 1
#     assert results["total"] == 1
#     assert results["total_pages"] == 1
#     assert type(results["items"]) is list
#     assert results["items"][0].id == expected[0]
#     assert results["items"][0].title == expected[1]
#     assert results["items"][0].description == expected[2]
#     assert results["items"][0].user_id == expected[4]
#
#
# @pytest.mark.run(order=3)
# @pytest.mark.parametrize(
#     "model_class,filter_type,column,column_value,method",
#     (
#             (models.User, "", "id", 1, "list"),
#             (models.User, "column_valu", "id", 1, "list"),
#             (models.Advertisement, "", "id", 1, "list"),
#             (models.Advertisement, "column_valu", "id", 1, "list"),
#     )
# )
# def test_filter_model_instances_with_incorrect_filter_type(session_maker, model_class, filter_type, column,
#                                                            column_value, method):
#     session = session_maker
#     with session() as sess:
#         filter_object = app.filtering.Filter(session=sess)
#     if method == "list":
#         with pytest.raises(HttpError) as exc_info:
#             filter_object.get_list(model_class=model_class,
#                                    filter_type=filter_type,  # type:ignore
#                                    column=column,  # type: ignore
#                                    column_value=column_value)
#     assert exc_info.type is HttpError
#     assert exc_info.value.status_code == 400
#     assert exc_info.value.description == "Unexpected or missing 'filter_type' parameter."
#
#
# @pytest.mark.run(order=4)
# @pytest.mark.parametrize(
#     "model_class, filter_type, column, column_value",
#     (
#             (models.Advertisement, "column_value", "incorrect", 1),
#             (models.User, "column_value", "incorrect", 1),
#             (models.Advertisement, "search_text", "incorrect", 1),
#             (models.User, "search_advs_by_text", "incorrect", 1),
#             (models.User, "date", "", "2024.11.26")
#     )
# )
# def test_filter_model_instances_with_incorrect_column(session_maker, model_class, filter_type, column, column_value):
#     session = session_maker
#     with session() as sess:
#         filter_object = app.filtering.Filter(session=sess)
#         with pytest.raises(HttpError) as exc_info:
#             filter_object.get_list(model_class=model_class,
#                                    filter_type=filter_type,  # type: ignore
#                                    column=column,  # type: ignore
#                                    column_value=column_value)
#     assert exc_info.type is HttpError
#     assert exc_info.value.status_code == 400
#     assert exc_info.value.description == "Unexpected 'column' parameter."
