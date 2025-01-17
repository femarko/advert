import pytest

import app.repository.filtering
from app.models import User, Advertisement
import app.errors
from tests.conftest import engine, session_maker, test_date, create_test_users_and_advs


@pytest.mark.parametrize(
    "params",
    ({"model_class": User, "filter_type": "column_value", "comparison": ">=", "column": "id", "column_value": "1000"},
     {"model_class": Advertisement,
      "filter_type": "column_value",
      "comparison": ">=",
      "column": "id",
      "column_value": "1000"},
     {"model_class": User, "filter_type": "search_text", "column": "name", "column_value": "st_f"},
     {"model_class": Advertisement,
      "filter_type": "search_text",
      "column": "description",
      "column_value": "st_f"},
     {"model_class": User,
      "filter_type": "search_text",
      "comparison": ">=",
      "column": "name",
      "column_value": "st_f"},
     {"model_class": Advertisement,
      "filter_type": "search_text",
      "comparison": ">=",
      "column": "description",
      "column_value": "st_f"},
     {"model_class": User,
      "filter_type": "column_value",
      "column": "creation_date",
      "column_value": "1900-01-01",
      "comparison": "<="},
     {"model_class": Advertisement,
      "filter_type": "column_value",
      "column": "creation_date",
      "column_value": "1900-01-01",
      "comparison": "<="},
     {"model_class": User,
      "filter_type": "search_text",
      "column": "email",
      "column_value": "st_f",
      "comparison": ""},
     {"model_class": Advertisement,
      "filter_type": "search_text",
      "column": "title",
      "column_value": "ilt",
      "comparison":""},
     {"model_class": User,
      "filter_type": "column_value",
      "column": "id",
      "column_value": "1000",
      "comparison": ">="},
     {"model_class": Advertisement,
      "filter_type": "column_value",
      "column": "user_id",
      "column_value": "1000",
      "comparison": ">="}))
def test_filter_and_return_paginated_data_with_correct_params(
        session_maker, create_test_users_and_advs, params, test_date
):
    session = session_maker
    with session() as sess:
        filter_result = app.repository.filtering.get_list_or_paginated_data(session=sess, paginate=True, **params)
    assert filter_result["page"] == 1
    assert filter_result["per_page"] == 10
    assert filter_result["total_pages"] == 1
    assert type(filter_result["items"]) == list
    assert set([(item["creation_date"]) for item in filter_result["items"]]) == {test_date.isoformat()}
    if params["model_class"] is User:
        assert filter_result["total"] == 2
        assert len(filter_result["items"]) == 2
        assert set([item["id"] for item in filter_result["items"]]) == {1000, 1001}
    else:
        assert filter_result["total"] == 4
        assert len(filter_result["items"]) == 4
        assert set([item["id"] for item in filter_result["items"]]) == {1000, 1001, 1003, 1004}


def test_filter_and_return_paginated_data_all_params_are_wrong(session_maker):
    params = {"model_class": "wrong_param",
              "filter_type": "wrong_param",
              "comparison": "wrong_param",
              "column": "wrong_param",
              "column_value": "wrong_param"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **params)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'model_class'. Valid values: "
        f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
        f"'wrong_param' is invalid value for 'comparison'. "
        f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
        f'\'wrong_param\' is invalid value for \'column\'. Valid values: '
        f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
        f'"for <class \'app.models.Advertisement\'>": '
        f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'
    }


def test_filter_and_return_paginated_data_all_params_are_missing(session_maker):
    params = {}
    session = session_maker
    with pytest.raises(expected_exception=app.errors.ValidationError) as e:
        with session() as sess:
            app.repository.filtering.get_list_or_paginated_data(session=sess, **params)
    assert e.type == app.errors.ValidationError
    assert set(e.value.args[0]) == {f"Value for 'model_class' is not found.",
                                    f"Value for 'filter_type' is not found.",
                                    f"Value for 'column' is not found.",
                                    f"Value for 'comparison' is not found."}


def test_filter_and_return_paginated_data_all_params_are_empty_strings(session_maker):
    data = {"model_class": "",
            "filter_type": "",
            "comparison": "",
            "column": "",
            "column_value": ""}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'' is invalid value for 'model_class'. Valid values: "
        f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f"'' is invalid value for 'filter_type'. "
        f"Valid values: ['column_value', 'search_text'].",
        f"'' is invalid value for 'comparison'. "
        f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
        f'\'\' is invalid value for \'column\'. Valid values: '
        f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
        f'"for <class \'app.models.Advertisement\'>": '
        f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'
    }


def test_filter_and_return_paginated_data_wrong__model_class(session_maker):
    data = {"model_class": "wrong_param",
            "filter_type": "column_value",
            "comparison": "is",
            "column": "name",
            "column_value": "test_filter_1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {f"'wrong_param' is invalid value for 'model_class'. "
                                    f"Valid values: [<class 'app.models.User'>, <class 'app.models.Advertisement'>]."}


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_filter_and_return_paginated_data_wrong__filter_type(session_maker, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": column,
            "column_value": "test_filter_1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {f"'wrong_param' is invalid value for 'filter_type'. "
                                    f"Valid values: ['column_value', 'search_text']."}


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_filter_and_return_paginated_data_wrong__comparison(session_maker, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "wrong_param",
            "column": column,
            "column_value": "test_filter_1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {f"'wrong_param' is invalid value for 'comparison'. "
                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_filter_and_return_paginated_data_wrong__column(session_maker, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "test_filter_1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."}


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_filter_and_return_paginated_data_wrong__column_value(session_maker, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "is",
            "column": column,
            "column_value": "wrong_param"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "OK"
    assert filter_result.errors is None
    assert filter_result.result == {'page': 1, 'per_page': 10, 'total': 0, 'total_pages': 0, 'items': []}


def test_filter_and_return_paginated_data_wrong__model_class__filter_type(session_maker):
    data = {"model_class": "wrong_param",
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": "name",
            "column_value": "test_filter_1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'model_class'. Valid values: "
        f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text']."
    }


def test_filter_and_return_paginated_data_wrong__model_class__comparison(session_maker):
    data = {"model_class": "wrong_param",
            "filter_type": "column_value",
            "comparison": "wrong_param",
            "column": "name",
            "column_value": "test_filter_1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'model_class'. Valid values: "
        f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."
    }


def test_filter_and_return_paginated_data_wrong__model_class__column(session_maker):
    data = {"model_class": "wrong_param",
            "filter_type": "column_value",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "test_filter_1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'model_class'. Valid values: "
        f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f'\'wrong_param\' is invalid value for \'column\'. Valid values: '
        f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
        f'"for <class \'app.models.Advertisement\'>": '
        f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'
    }


def test_filter_and_return_paginated_data_wrong__model_class__column_value(session_maker):
    data = {"model_class": "wrong_param",
            "filter_type": "column_value",
            "comparison": "is",
            "column": "name",
            "column_value": "wrong_param"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {f"'wrong_param' is invalid value for 'model_class'. Valid values: "
                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>]."}


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_filter_and_return_paginated_data_wrong__filter_type__comparison(session_maker, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "wrong_param",
            "comparison": "wrong_param",
            "column": column,
            "column_value": "test_filter_1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
        f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."
    }


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_filter_and_return_paginated_data_wrong__filter_type__column(session_maker, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "test_filter_1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
        f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."
    }


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_filter_and_return_paginated_data_wrong__filter_type__column_value(session_maker, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": column,
            "column_value": "wrong_param"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text']."
    }


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_filter_and_return_paginated_data_wrong__comparison__column(session_maker, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "wrong_param",
            "column": "wrong_param",
            "column_value": "test_filter_1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
        f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."
    }


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_filter_and_return_paginated_data_wrong__comparison__column_value(session_maker, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "wrong_param",
            "column": column,
            "column_value": "wrong_param"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."
    }


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_filter_and_return_paginated_data_wrong__column__column_value(session_maker, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "wrong_param"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."}


@pytest.mark.parametrize("column", ("name", "title"))
def test_filter_and_return_paginated_data_wrong__model_class__filter_type__comparison(session_maker, column):
    data = {"model_class": "wrong_param",
            "filter_type": "wrong_param",
            "comparison": "wrong_param",
            "column": column,
            "column_value": "test_filter_1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'model_class'. Valid values: "
        f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
        f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."
    }


def test_filter_and_return_paginated_data_wrong__model_class__filter_type__column(session_maker):
    data = {"model_class": "wrong_param",
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "test_filter_1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'model_class'. "
        f"Valid values: [<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
        f'\'wrong_param\' is invalid value for \'column\'. Valid values: '
        f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
        f'"for <class \'app.models.Advertisement\'>": '
        f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'
    }


@pytest.mark.parametrize("column", ("name", "title"))
def test_filter_and_return_paginated_data_wrong__model_class__filter_type__column_value(session_maker, column):
    data = {"model_class": "wrong_param",
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": column,
            "column_value": "wrong_param"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'model_class'. "
        f"Valid values: [<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
    }


@pytest.mark.parametrize("column", ("name", "title"))
def test_filter_and_return_paginated_data_wrong__model_class__comparison__column_value(session_maker, column):
    data = {"model_class": "wrong_param",
            "filter_type": "column_value",
            "comparison": "wrong_param",
            "column": column,
            "column_value": "wrong_param"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'model_class'. Valid values: "
        f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."
    }


def test_filter_and_return_paginated_data_wrong__model_class__column__column_value(session_maker):
    data = {"model_class": "wrong_param",
            "filter_type": "column_value",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "wrong_param"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'model_class'. "
        f"Valid values: [<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f'\'wrong_param\' is invalid value for \'column\'. Valid values: '
        f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
        f'"for <class \'app.models.Advertisement\'>": '
        f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'
    }


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_filter_and_return_paginated_data_wrong__filter_type__comparison__column_value(session_maker, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "wrong_param",
            "comparison": "wrong_param",
            "column": column,
            "column_value": "wrong_param"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
        f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."
    }


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_filter_and_return_paginated_data_wrong__filter_type__column__column_value(session_maker, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "wrong_param"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
        f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."
    }


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_filter_and_return_paginated_data_wrong__comparison__column__column_value(session_maker, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "wrong_param",
            "column": "wrong_param",
            "column_value": "wrong_param"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
        f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."
    }


@pytest.mark.parametrize("model_class,column", ((User, 'id'), (Advertisement, 'id'), (Advertisement, 'user_id')))
def test_filter_and_return_paginated_data_nondigit_characters_as__id__user_id(session_maker, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "is",
            "column": column,
            "column_value": "wrong_param"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {f"'{column}' must be a digit."}


@pytest.mark.parametrize("model_class,wrong_date", ((User, "non_date_value"),
                                                    (Advertisement, "non_date_value"),
                                                    (User, 2024),
                                                    (Advertisement, 2024),
                                                    (User, "01/01/2024"),
                                                    (Advertisement, "01/01/2024")))
def test_filter_and_return_paginated_data_wrong_data_format_as__creation_date(session_maker, model_class, wrong_date):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "is",
            "column": "creation_date",
            "column_value": wrong_date}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"When column='creation_date', 'column_value' must be a date string of the following format: 'YYYY-MM-DD'."
    }


@pytest.mark.parametrize("model_class,comparison,column", ((User, ">", "name"),
                                                           (User, ">=", "name"),
                                                           (User, "<", "name"),
                                                           (User, "<=", "name"),
                                                           (User, ">", "email"),
                                                           (User, ">=", "email"),
                                                           (User, "<", "email"),
                                                           (User, "<=", "email"),
                                                           (Advertisement, ">", "title"),
                                                           (Advertisement, ">=", "title"),
                                                           (Advertisement, "<", "title"),
                                                           (Advertisement, "<=", "title"),
                                                           (Advertisement, ">", "description"),
                                                           (Advertisement, ">=", "description"),
                                                           (Advertisement, "<", "description"),
                                                           (Advertisement, "<=", "description")))
def test_filter_and_return_paginated_data_wrong_comparison_for_text_fields(session_maker, model_class, comparison, column):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": comparison,
            "column": column,
            "column_value": "test_filter_1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        f"'{comparison}' is invalid value for 'comparison'. Valid values: ['is', 'is_not']."
    }


@pytest.mark.parametrize("model_class,column", ((User, "id"), (Advertisement, "id"), (Advertisement, "user_id")))
def test_filter_and_return_paginated_data_unexpected_columns_with__search_text__filter_type(session_maker, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "search_text",
            "comparison": "",
            "column": column,
            "column_value": "1000"}
    session = session_maker
    with session() as sess:
        filter_result = filter_and_return_paginated_data(session=sess, **data)
    assert isinstance(filter_result, FilterResult)
    assert filter_result.status == "Failed"
    assert filter_result.result is None
    assert filter_result.errors == {
        "For filter_type='search_text' the folowing columns are available: "
        "{for <class 'app.models.User'>: [name, email], for <class 'app.models.Advertisement'>: [title, description]}"
    }

# @pytest.mark.parametrize("creation_date_value", ("01.01.1900", "01/01/1900", "1-1-1900"))
# def test_filter_and_return_paginated_data_with_wrong_creation_data_format_as_column_value_parameter(
#         session_maker, create_test_users_and_advs, creation_date_value
# ):
#     session = session_maker
#     with session() as sess:
#         filter_result = filter_and_return_paginated_data(session=sess,
#                                                                        model_class=models.Advertisement,  # type: ignore
#                                                                        filter_type="column_value",  # type: ignore
#                                                                        column="creation_date",  # type: ignore
#                                                                        comparison="is",  # type: ignore
#                                                                        column_value=creation_date_value)  # type: ignore
#     assert filter_result.status == "Failed"
#     assert filter_result.errors == [f"time data '{creation_date_value}' does not match format '%Y-%m-%d'"]
#     assert filter_result.result is None
#
#
# def test_filter_and_return_paginated_data_with_wrong_comparison_and_column_parameters(
#         session_maker, create_test_users_and_advs, test_date
# ):
#     session = session_maker
#     with session() as sess:
#         filter_result = filter_and_return_paginated_data(session=sess,
#                                                                        model_class=models.Advertisement,  # type: ignore
#                                                                        filter_type="column_value",  # type: ignore
#                                                                        column="wrong_column",  # type: ignore
#                                                                        comparison="wrong_comparison",  # type: ignore
#                                                                        column_value="test_filter")  # type: ignore
#     assert filter_result.status == "Failed"
#     assert filter_result.errors == ["Unexpected or missing 'column' parameter.",
#                                     "Unexpected or missing 'comparison' parameter."]
#     assert filter_result.result is None
#
#
# def test_filter_and_return_paginated_data_with_wrong_filter_type_parameter(
#         session_maker, create_test_users_and_advs, test_date
# ):
#     session = session_maker
#     with session() as sess:
#         filter_result = filter_and_return_paginated_data(session=sess,
#                                                                        model_class=models.Advertisement,  # type: ignore
#                                                                        filter_type="wrong_filter_type",  # type: ignore
#                                                                        column="id",  # type: ignore
#                                                                        comparison="is",  # type: ignore
#                                                                        column_value="1000")  # type: ignore
#     assert filter_result.status == "Failed"
#     assert filter_result.errors == ["Unexpected or missing 'filter_type' parameter."]
#     assert filter_result.result is None
