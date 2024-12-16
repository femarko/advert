import pytest
from app.filtering import Filter, Params, ValidParams
from app.models import Advertisement, User


@pytest.fixture(scope="module")
def fake_session():
    return ...


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


def test_model_class_is_wrong_param(fake_session):
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
def test_filter_type_is_wrong_param(fake_session, model_class, column):
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
def test_comparison_is_wrong_param(fake_session, model_class, column):
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
def test_column_is_wrong_param(fake_session, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "test_filter_1000"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."}


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_column_value_is_wrong_param(fake_session, model_class, column):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "is",
            "column": column,
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == set()


def test_model_class_and_filter_type_are_wrong_params(fake_session):
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


def test_model_class_and_comparison_are_wrong_params(fake_session):
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


def test_model_class_and_column_are_wrong_params(fake_session):
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


def test_model_class_and_column_value_are_wrong_params(fake_session):
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
def test_filter_type_and_comparison_are_wrong_params(fake_session, model_class, column):
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
def test_filter_type_and_column_are_wrong_params(fake_session, model_class, columns):
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
def test_filter_type_and_column_value_are_wrong_params(fake_session, model_class, column):
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
def test_comparison_and_column_are_wrong_params(fake_session, model_class, columns):
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
def test_comparison_and_column_value_are_wrong_params(fake_session, model_class, column):
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
def test_column_and_column_value_are_wrong_params(fake_session, model_class, columns):
    data = {"model_class": model_class,
            "filter_type": "column_value",
            "comparison": "is",
            "column": "wrong_param",
            "column_value": "wrong_param"}
    filter_object = Filter(session=fake_session)
    filter_object.validate_params(data=data, params=Params)
    assert filter_object.errors == {f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."}

# def test_model_class_is_wrong_param(fake_session):
#     data =
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors ==
