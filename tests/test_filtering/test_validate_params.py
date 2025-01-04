import pytest
from app.repository.filtering import Filter, Params
from app.models import Advertisement, User


@pytest.fixture(scope="module")
def fake_session():
    return ...


@pytest.mark.parametrize(
    "params",
    ({"model_class": User, "filter_type": "column_value", "comparison": ">=", "column": "id", "column_value": "1000"},
     {"model_class": Advertisement,
      "filter_type": "column_value",
      "comparison": ">=",
      "column": "id",
      "column_value": "1000"},
     {"model_class": User, "filter_type": "search_text", "column": "name", "column_value": "test"},
     {"model_class": Advertisement, "filter_type": "search_text", "column": "description", "column_value": "test"},
     {"model_class": User, "filter_type": "search_text", "comparison": ">=", "column": "name", "column_value": "test"},
     {"model_class": Advertisement,
      "filter_type": "search_text",
      "comparison": ">=",
      "column": "description",
      "column_value": "test"}
     )
)
def test_filter_validate_params_with_correct_params(fake_session, params):
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=params, params=Params)
    assert filter_object.errors == set()


def test_all_params_are_wrong(fake_session):
    data = {"model_class": "wrong_param",
            "filter_type": "wrong_param",
            "comparison": "wrong_param",
            "column": "wrong_param",
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {
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


def test_all_params_are_missing(fake_session):
    data = {}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"Value for 'model_class' is not found.",
                                    f"Value for 'filter_type' is not found.",
                                    f"Value for 'comparison' is not found.",
                                    f"Value for 'column' is not found."}


def test_all_params_are_empty_strings():
    data = {"model_class": "",
            "filter_type": "",
            "comparison": "",
            "column": "",
            "column_value": ""}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {
        f"'' is invalid value for 'model_class'. Valid values: "
        f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f"'' is invalid value for 'filter_type'. "
        f"Valid values: ['column_value', 'search_text'].",
        f"'' is invalid value for 'comparison'. "
        f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
        f'\'\' is invalid value for \'column\'. Valid values: '
        f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
        f'"for <class \'app.models.Advertisement\'>": '
        f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'}


def test_wrong__model_class(fake_session):
    data = {"model_class": "wrong_param",
            "filter_type": "column_value",
            "comparison": "is",
            "column": "name",
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'model_class'. "
                                    f"Valid values: [<class 'app.models.User'>, <class 'app.models.Advertisement'>]."}


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_wrong__filter_type(fake_session, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": column,
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'filter_type'. "
                                    f"Valid values: ['column_value', 'search_text']."}


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_wrong__comparison(fake_session, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "wrong_param",
            "column": column,
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'comparison'. "
                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_wrong__column(fake_session, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."}


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_wrong__column_value(fake_session, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "is",
            "column": column,
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == set()


def test_wrong__model_class__filter_type(fake_session):
    data = {"model_class": "wrong_param",
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": "name",
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'model_class'. "
                                    f"Valid values: "
                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
                                    f"'wrong_param' is invalid value for 'filter_type'. "
                                    f"Valid values: ['column_value', 'search_text']."}


def test_wrong__model_class__comparison(fake_session):
    data = {"model_class": "wrong_param",
            "filter_type": "column_value",
            "comparison": "wrong_param",
            "column": "name",
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'model_class'. "
                                    f"Valid values: "
                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
                                    f"'wrong_param' is invalid value for 'comparison'. "
                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}


def test_wrong__model_class__column(fake_session):
    data = {"model_class": "wrong_param",
            "filter_type": "column_value",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {
        f"'wrong_param' is invalid value for 'model_class'. Valid values: "
        f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f'\'wrong_param\' is invalid value for \'column\'. Valid values: '
        f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
        f'"for <class \'app.models.Advertisement\'>": '
        f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'
    }


def test_wrong__model_class__column_value(fake_session):
    data = {"model_class": "wrong_param",
            "filter_type": "column_value",
            "comparison": "is",
            "column": "name",
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'model_class'. Valid values: "
                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>]."}


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_wrong__filter_type__comparison(fake_session, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "wrong_param",
            "comparison": "wrong_param",
            "column": column,
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'filter_type'. "
                                    f"Valid values: ['column_value', 'search_text'].",
                                    f"'wrong_param' is invalid value for 'comparison'. "
                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_wrong__filter_type__column(fake_session, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'filter_type'. "
                                    f"Valid values: ['column_value', 'search_text'].",
                                    f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."}


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_wrong__filter_type__column_value(fake_session, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": column,
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'filter_type'. "
                                    f"Valid values: ['column_value', 'search_text']."}


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_wrong__comparison__column(fake_session, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "wrong_param",
            "column": "wrong_param",
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'comparison'. "
                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
                                    f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."}


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_wrong__comparison__column_value(fake_session, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "wrong_param",
            "column": column,
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'comparison'. "
                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_wrong__column__column_value(fake_session, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."}


@pytest.mark.parametrize("column", ("name", "title"))
def test_wrong__model_class__filter_type__comparison(fake_session, column):
    data = {"model_class": "wrong_param",
            "filter_type": "wrong_param",
            "comparison": "wrong_param",
            "column": column,
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'model_class'. "
                                    f"Valid values: "
                                    f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
                                    f"'wrong_param' is invalid value for 'filter_type'. "
                                    f"Valid values: ['column_value', 'search_text'].",
                                    f"'wrong_param' is invalid value for 'comparison'. "
                                    f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}


def test_wrong__model_class__filter_type__column(fake_session):
    data = {"model_class": "wrong_param",
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {
        f"'wrong_param' is invalid value for 'model_class'. "
        f"Valid values: [<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
        f'\'wrong_param\' is invalid value for \'column\'. Valid values: '
        f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
        f'"for <class \'app.models.Advertisement\'>": '
        f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'
    }


@pytest.mark.parametrize("column", ("name", "title"))
def test_wrong__model_class__filter_type__column_value(fake_session, column):
    data = {"model_class": "wrong_param",
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": column,
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {
        f"'wrong_param' is invalid value for 'model_class'. "
        f"Valid values: [<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
    }


@pytest.mark.parametrize("column", ("name", "title"))
def test_wrong__model_class__comparison__column_value(fake_session, column):
    data = {"model_class": "wrong_param",
            "filter_type": "column_value",
            "comparison": "wrong_param",
            "column": column,
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {
        f"'wrong_param' is invalid value for 'model_class'. Valid values: "
        f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."
    }


def test_wrong__model_class__column__column_value(fake_session):
    data = {"model_class": "wrong_param",
            "filter_type": "column_value",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {
        f"'wrong_param' is invalid value for 'model_class'. "
        f"Valid values: [<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
        f'\'wrong_param\' is invalid value for \'column\'. Valid values: '
        f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
        f'"for <class \'app.models.Advertisement\'>": '
        f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'
    }


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_wrong__filter_type__comparison__column_value(fake_session, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "wrong_param",
            "comparison": "wrong_param",
            "column": column,
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
        f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."
    }


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_wrong__filter_type__column__column_value(fake_session, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "wrong_param",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {
        f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
        f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."
    }


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_wrong__comparison__column__column_value(fake_session, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "wrong_param",
            "column": "wrong_param",
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {
        f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
        f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."
    }


@pytest.mark.parametrize("model_class,column", ((User, 'id'), (Advertisement, 'id'), (Advertisement, 'user_id')))
def test_nondigit_characters_as__id__user_id(fake_session, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "is",
            "column": column,
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'{column}' must be a digit."}


@pytest.mark.parametrize("model_class,wrong_date", ((User, "non_date_value"),
                                                    (Advertisement, "non_date_value"),
                                                    (User, 2024),
                                                    (Advertisement, 2024),
                                                    (User, "01/01/2024"),
                                                    (Advertisement, "01/01/2024")))
def test_wrong_data_format_as__creation_date(fake_session, model_class, wrong_date):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "is",
            "column": "creation_date",
            "column_value": wrong_date}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"When column='creation_date', 'column_value' must be a date "
                                    f"string of the following format: 'YYYY-MM-DD'."}


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
def test_wrong_comparison_for_text_fields(fake_session, model_class, comparison, column):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": comparison,
            "column": column,
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {
        f"'{comparison}' is invalid value for 'comparison'. Valid values: ['is', 'is_not']."
    }


@pytest.mark.parametrize("model_class,column", ((User, "id"), (Advertisement, "id"), (Advertisement, "user_id")))
def test_unexpected_columns_with__search_text__filter_type(fake_session, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "search_text",
            "comparison": "",
            "column": column,
            "column_value": "1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {
        "For filter_type='search_text' the folowing columns are available: "
        "{for <class 'app.models.User'>: [name, email], for <class 'app.models.Advertisement'>: [title, description]}"
    }
