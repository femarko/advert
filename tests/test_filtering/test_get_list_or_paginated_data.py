import pytest
import app.errors
import app.repository
import app.repository.filtering
from app import services, models
from app.models import User, Advertisement


def test_get_list_or_paginated_data_returns_list_when_all_params_are_correct_and_paginate_is_omitted(
        session_maker, create_test_users_and_advs, test_date
):
    session = session_maker
    with session() as s:
        result = app.repository.filtering.get_list_or_paginated_data(
            session=s,
            model_class=models.User,
            filter_type="search_text", comparison="is", column="name",  # type: ignore
            column_value="1000"
        )
    result_params = services.get_params(result[0])
    assert result_params == {"id": 1000,
                             "name": "test_filter_1000",
                             "email": "test_filter_1000@email.com",
                             "creation_date": test_date.isoformat()}


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
def test_get_list_or_paginated_data_returns_paginated_data_with_correct_params(
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


def test_get_list_or_paginated_data_returns_dict_when_all_params_are_correct_and_paginate_is_true(
        session_maker, create_test_users_and_advs, test_date
):
    session = session_maker
    with session() as s:
        result = app.repository.filtering.get_list_or_paginated_data(
            session=s,
            model_class=models.User,
            filter_type="search_text", comparison="is", column="name",  # type: ignore
            column_value="1000",
            paginate=True
        )
    assert result == {
        'page': 1,
        'per_page': 10,
        'total': 1,
        'total_pages': 1,
        'items': [
            {
                'id': 1000,
                'name': 'test_filter_1000',
                'email': 'test_filter_1000@email.com',
                'creation_date': '1900-01-01T00:00:00'
            }
        ]
    }


def test_get_list_or_paginated_data_raises_error_when_invalid_params_are_passed(
        session_maker, create_test_users_and_advs, test_date
):
    session = session_maker
    with session() as s:
        with pytest.raises(expected_exception=app.errors.ValidationError) as e:
            app.repository.filtering.get_list_or_paginated_data(
                session=s,
                model_class="INVALID", filter_type="INVALID", comparison="INVALID", column="INVALID",  # type: ignore
                column_value="INVALID"
            )
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert e.value.message["params_passed"] == {'model_class': 'INVALID',
                                                'filter_type': 'INVALID',
                                                'comparison': 'INVALID',
                                                'column': 'INVALID',
                                                'column_value': 'INVALID'}
    assert set(e.value.message["invalid_params"].keys()) == {"model_class", "filter_type", "column", "comparison"}
    assert set(e.value.message["invalid_params"]["model_class"]) == set(
        "Valid values are: [<class 'app.models.User'>, <class 'app.models.Advertisement'>]"
    )
    assert set(e.value.message["invalid_params"]["filter_type"]) == set(
        "Valid values are: ['column_value', 'search_text']"
    )
    assert set(e.value.message["invalid_params"]["column"]) == set(
        "Valid values are: ['description', 'title', 'email', 'user_id', 'name', 'creation_date', 'id']"
    )
    assert set(e.value.message["invalid_params"]["comparison"]) == set(
        "Valid values are: ['is', 'is_not', '<', '>', '>=', '<=']"
    )


def test_get_list_or_paginated_data_raises_error_when_all_params_are_missing(
        session_maker, create_test_users_and_advs, test_date
):
    session = session_maker
    with session() as s:
        with pytest.raises(expected_exception=app.errors.ValidationError) as e:
            app.repository.filtering.get_list_or_paginated_data(session=s)
    assert set(e.value.message.keys()) == {"params_passed", "missing_params"}
    assert e.value.message["params_passed"] == {}
    assert set(e.value.message["missing_params"]) == {
        "model_class", "filter_type", "column", "column_value", "comparison"
    }
