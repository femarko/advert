import app.repository.filtering
from app import services, models


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
