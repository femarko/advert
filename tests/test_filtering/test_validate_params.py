import pytest

import app.errors
from app.repository.filtering import Filter, Params
from app.models import Advertisement, User, ModelClasses


def test_validate_params_does_not_raise_validation_error_when_all_params_are_correct():
    data = {"model_class": Advertisement, "filter_type": "column_value", "comparison": ">=", "column": "id",
            "column_value": "1000"}
    filter_instance = Filter("fake_session")
    filter_instance._validate_params(data=data, params=Params)
    assert filter_instance.params_info.logs == set()
    assert filter_instance.params_info.missing_params == []
    assert filter_instance.params_info.invalid_params == {}


@pytest.mark.parametrize(
    "data", (
            {"model_class": Advertisement, "filter_type": "search_text", "column": "description",
             "column_value": "test"},
            {"model_class": User, "filter_type": "search_text", "comparison": "INVALID", "column": "name",
             "column_value": "test"},
            {"model_class": Advertisement, "filter_type": "search_text", "comparison": ">=", "column": "description",
             "column_value": "test"}
    )
)
def test_validate_params_does_not_raise_error_when_filter_type_is_search_text_and_comparison_is_missing_or_invalid(
        data
):
    filter_instance = Filter("fake_session")
    filter_instance._validate_params(data=data, params=Params)
    assert filter_instance.params_info.logs == set()
    assert filter_instance.params_info.missing_params == []
    assert filter_instance.params_info.invalid_params == {}


def test_validate_params_raises_validation_error_when_model_class_is_missing_and_comparison_is_invalid():
    data = {"filter_type": "column_value", "comparison": ">", "column": "name", "column_value": True}
    with pytest.raises(app.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert e.value.message["params_passed"] == data
    assert e.value.message["missing_params"] == ["model_class"]
    assert e.value.message["invalid_params"] == {
        'comparison': 'When "filter_type is "column_value", valid values for "comparison" are: [\'is\', \'is_not\']'
    }


def test_validate_params_raises_validation_error_when_filter_type_is_search_text_and_column_is_id():
    data = {"model_class": User, "filter_type": "search_text", "column": "id", "column_value": "text"}
    with pytest.raises(app.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert e.value.message["params_passed"] == data
    assert e.value.message.get("missing_params") is None
    assert e.value.message["invalid_params"] == {
        'column': 'For model class "<class \'app.models.User\'>" text search is available '
                  'in the following columns: [\'name\', \'email\'].'
    }


def test_validate_params_raises_validation_error_when_filter_type_is_column_value_column_is_id_and_column_value_is_str():
    data = {"model_class": User, "filter_type": "column_value", "column": "id", "column_value": "text"}
    with pytest.raises(app.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert e.value.message["params_passed"] == data
    assert e.value.message.get("missing_params") == ['comparison']
    assert e.value.message["invalid_params"] == {
        'column_value': 'When "column" is "id", "column_value" must be a digit.'
    }


def test_validate_params_raises_validation_error_when_filter_type_and_comparison_are_missing():
    data = {"model_class": User, "column": "id", "column_value": "text"}
    with pytest.raises(app.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert e.value.message["params_passed"] == data
    assert e.value.message.get("missing_params") == ['filter_type', 'comparison']


def test_validate_params_raises_validation_error_when_filter_type_is_text_search_column_is_creation_date_mc_is_user():
    data = {
        "model_class": User, "filter_type": "search_text", "column": "creation_date", "column_value": "2025-01-01",
        "comparison": "is"
    }
    with pytest.raises(app.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert e.value.message["params_passed"] == data
    assert e.value.message.get("missing_params") is None
    assert e.value.message["invalid_params"] == {
        'column': 'For model class "<class \'app.models.User\'>" text search is available '
                  'in the following columns: [\'name\', \'email\'].'
    }


def test_validate_params_raises_validation_error_when_filter_type_is_text_search_column_is_creation_date_mc_is_adv():
    data = {"model_class": Advertisement, "filter_type": "search_text", "column": "creation_date",
            "column_value": "2025-01-01", "comparison": "is"}
    with pytest.raises(app.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert e.value.message["params_passed"] == data
    assert e.value.message.get("missing_params") is None
    assert e.value.message["invalid_params"] == {
        'column': f'For model class "<class \'app.models.Advertisement\'>" text search is available in the following '
                  f'columns: [\'title\', \'description\'].'
    }


def test_validate_params_raises_validation_error_when_wrong_column_for_model_class_adv_is_passed():
    data = {
        "model_class": Advertisement, "filter_type": "column_value", "column": "wrong", "column_value": "2025-01-01",
        "comparison": "is"
    }
    with pytest.raises(app.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert e.value.message["params_passed"] == data
    assert e.value.message.get("missing_params") is None
    assert e.value.message["invalid_params"] == {
        'column': 'For model class "<class \'app.models.Advertisement\'>" valid values for "column" are: '
                  '[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\'].'
    }


def test_validate_params_raises_validation_error_when_column_for_model_class_adv_is_wrong_and_filter_type_missing():
    data = {"model_class": Advertisement, "column": "wrong", "column_value": "2025-01-01", "comparison": "is"}
    with pytest.raises(app.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert e.value.message["params_passed"] == data
    assert e.value.message.get("missing_params") == ['filter_type']
    assert e.value.message["invalid_params"] == {
        'column': 'For model class "<class \'app.models.Advertisement\'>" valid values for "column" are: '
                  '[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\'].'
    }


def test_validate_params_raises_validation_error_when_filter_type_is_search_text_and_column_is_wrong():
    data = {
        "model_class": Advertisement, "filter_type": "search_text", "column": "wrong", "column_value": "2025-01-01",
        "comparison": "is"
    }
    with pytest.raises(app.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert e.value.message["params_passed"] == data
    assert e.value.message.get("missing_params") is None
    assert e.value.message["invalid_params"] == {
        'column': f'For model class "<class \'app.models.Advertisement\'>" text search is available '
                  f'in the following columns: [\'title\', \'description\'].'
    }


def test_validate_params_raises_validation_error_when_all_params_are_missing():
    data = {}
    with pytest.raises(app.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert e.value.message["params_passed"] == data
    assert e.value.message.get("missing_params") == [
        'model_class', 'filter_type', 'column', 'column_value', 'comparison'
    ]
    assert e.value.message.get("invalid_params") is None


@pytest.mark.parametrize(
    "data",
    (
            {"model_class": "INVALID", "filter_type": "INVALID", "column": "INVALID", "column_value": "INVALID",
             "comparison": "INVALID"},
            {"model_class": "", "filter_type": "", "comparison": "", "column": "", "column_value": ""},
    )
)
def test_validate_params_raises_validation_error_when_all_params_are_invalid(data):

    with pytest.raises(app.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert e.value.message["params_passed"] == data
    assert e.value.message.get("missing_params") is None
    assert set(e.value.message["invalid_params"]["model_class"]) == set(
        "Valid values are: [<class ""'app.models.User'>, " f"<class 'app.models.Advertisement'>]"
    )
    assert set(e.value.message["invalid_params"]["filter_type"]) == set(
        "Valid values are: ['column_value', 'search_text']"
    )
    assert set(e.value.message["invalid_params"]["column"]) == set(
        "Valid values are: ['description', 'creation_date', 'user_id', 'name', 'email', 'id', 'title']"
    )
    assert set(e.value.message["invalid_params"]["comparison"]) == set(
        "Valid values are: ['is', 'is_not', '<', '>', '>=', '<=']"
    )


def test_validate_params_raises_validationerr_ignores_comparison_when_filter_type_is_search_text_and_column_is_wrong_():
    data = {
        "model_class": Advertisement, "filter_type": "search_text", "column": "wrong", "column_value": "2025-01-01",
        "comparison": ">>>>"
    }
    with pytest.raises(app.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert e.value.message["params_passed"] == data
    assert e.value.message.get("missing_params") is None
    assert e.value.message.get("invalid_params") == {
        'column': f'For model class "<class \'app.models.Advertisement\'>" text search is available '
                  f'in the following columns: [\'title\', \'description\'].'
    }


# def test_validate_params_raises_validationerr_when_():
#     data = {"model_class": Advertisement, "filter_type": "search_text", "comparison": ">=", "column": "description", "column_value": "test"}
#     with pytest.raises(app.errors.ValidationError) as e:
#         Filter("fake_session")._validate_params(data=data, params=Params)
#     assert e.value.message["params_passed"] == data
#     assert e.value.message.get("missing_params") is None
#     assert e.value.message.get("invalid_params") == {
#         'column': f'For model class "<class \'app.models.Advertisement\'>" text search is available '
#                   f'in the following columns: [\'title\', \'description\'].'
#     }


# def test_all_params_are_empty_strings():
#     data =
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {
#         f"'' is invalid value for 'model_class'. Valid values: "
#         f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
#         f"'' is invalid value for 'filter_type'. "
#         f"Valid values: ['column_value', 'search_text'].",
#         f"'' is invalid value for 'comparison'. "
#         f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
#         f'\'\' is invalid value for \'column\'. Valid values: '
#         f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
#         f'"for <class \'app.models.Advertisement\'>": '
#         f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'}
#
#
# def test_wrong__model_class(fake_session):
#     data = {"model_class": "wrong_param",
#             "filter_type": "column_value",
#             "comparison": "is",
#             "column": "name",
#             "column_value": "test_filter_1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'model_class'. "
#                                     f"Valid values: [<class 'app.models.User'>, <class 'app.models.Advertisement'>]."}
#
#
# @pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
# def test_wrong__filter_type(fake_session, model_class, column):
#     data = {"model_class": model_class,
#             "filter_type": "wrong_param",
#             "comparison": "is",
#             "column": column,
#             "column_value": "test_filter_1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'filter_type'. "
#                                     f"Valid values: ['column_value', 'search_text']."}
#
#
# @pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
# def test_wrong__comparison(fake_session, model_class, column):
#     data = {"model_class": model_class,
#             "filter_type": "column_value",
#             "comparison": "wrong_param",
#             "column": column,
#             "column_value": "test_filter_1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'comparison'. "
#                                     f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}
#
#
# @pytest.mark.parametrize("model_class,columns",
#                          ((User, ['id', 'name', 'email', 'creation_date']),
#                           (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
# def test_wrong__column(fake_session, model_class, columns):
#     data = {"model_class": model_class,
#             "filter_type": "column_value",
#             "comparison": "is",
#             "column": "wrong_param",
#             "column_value": "test_filter_1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."}
#
#
# @pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
# def test_wrong__column_value(fake_session, model_class, column):
#     data = {"model_class": model_class,
#             "filter_type": "column_value",
#             "comparison": "is",
#             "column": column,
#             "column_value": "wrong_param"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == set()
#
#
# def test_wrong__model_class__filter_type(fake_session):
#     data = {"model_class": "wrong_param",
#             "filter_type": "wrong_param",
#             "comparison": "is",
#             "column": "name",
#             "column_value": "test_filter_1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'model_class'. "
#                                     f"Valid values: "
#                                     f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
#                                     f"'wrong_param' is invalid value for 'filter_type'. "
#                                     f"Valid values: ['column_value', 'search_text']."}
#
#
# def test_wrong__model_class__comparison(fake_session):
#     data = {"model_class": "wrong_param",
#             "filter_type": "column_value",
#             "comparison": "wrong_param",
#             "column": "name",
#             "column_value": "test_filter_1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'model_class'. "
#                                     f"Valid values: "
#                                     f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
#                                     f"'wrong_param' is invalid value for 'comparison'. "
#                                     f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}
#
#
# def test_wrong__model_class__column(fake_session):
#     data = {"model_class": "wrong_param",
#             "filter_type": "column_value",
#             "comparison": "is",
#             "column": "wrong_param",
#             "column_value": "test_filter_1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {
#         f"'wrong_param' is invalid value for 'model_class'. Valid values: "
#         f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
#         f'\'wrong_param\' is invalid value for \'column\'. Valid values: '
#         f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
#         f'"for <class \'app.models.Advertisement\'>": '
#         f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'
#     }
#
#
# def test_wrong__model_class__column_value(fake_session):
#     data = {"model_class": "wrong_param",
#             "filter_type": "column_value",
#             "comparison": "is",
#             "column": "name",
#             "column_value": "wrong_param"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'model_class'. Valid values: "
#                                     f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>]."}
#
#
# @pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
# def test_wrong__filter_type__comparison(fake_session, model_class, column):
#     data = {"model_class": model_class,
#             "filter_type": "wrong_param",
#             "comparison": "wrong_param",
#             "column": column,
#             "column_value": "test_filter_1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'filter_type'. "
#                                     f"Valid values: ['column_value', 'search_text'].",
#                                     f"'wrong_param' is invalid value for 'comparison'. "
#                                     f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}
#
#
# @pytest.mark.parametrize("model_class,columns",
#                          ((User, ['id', 'name', 'email', 'creation_date']),
#                           (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
# def test_wrong__filter_type__column(fake_session, model_class, columns):
#     data = {"model_class": model_class,
#             "filter_type": "wrong_param",
#             "comparison": "is",
#             "column": "wrong_param",
#             "column_value": "test_filter_1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'filter_type'. "
#                                     f"Valid values: ['column_value', 'search_text'].",
#                                     f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."}
#
#
# @pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
# def test_wrong__filter_type__column_value(fake_session, model_class, column):
#     data = {"model_class": model_class,
#             "filter_type": "wrong_param",
#             "comparison": "is",
#             "column": column,
#             "column_value": "wrong_param"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'filter_type'. "
#                                     f"Valid values: ['column_value', 'search_text']."}
#
#
# @pytest.mark.parametrize("model_class,columns",
#                          ((User, ['id', 'name', 'email', 'creation_date']),
#                           (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
# def test_wrong__comparison__column(fake_session, model_class, columns):
#     data = {"model_class": model_class,
#             "filter_type": "column_value",
#             "comparison": "wrong_param",
#             "column": "wrong_param",
#             "column_value": "test_filter_1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'comparison'. "
#                                     f"Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
#                                     f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."}
#
#
# @pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
# def test_wrong__comparison__column_value(fake_session, model_class, column):
#     data = {"model_class": model_class,
#             "filter_type": "column_value",
#             "comparison": "wrong_param",
#             "column": column,
#             "column_value": "wrong_param"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'comparison'. "
#                                     f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}
#
#
# @pytest.mark.parametrize("model_class,columns",
#                          ((User, ['id', 'name', 'email', 'creation_date']),
#                           (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
# def test_wrong__column__column_value(fake_session, model_class, columns):
#     data = {"model_class": model_class,
#             "filter_type": "column_value",
#             "comparison": "is",
#             "column": "wrong_param",
#             "column_value": "wrong_param"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."}
#
#
# @pytest.mark.parametrize("column", ("name", "title"))
# def test_wrong__model_class__filter_type__comparison(fake_session, column):
#     data = {"model_class": "wrong_param",
#             "filter_type": "wrong_param",
#             "comparison": "wrong_param",
#             "column": column,
#             "column_value": "test_filter_1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'wrong_param' is invalid value for 'model_class'. "
#                                     f"Valid values: "
#                                     f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
#                                     f"'wrong_param' is invalid value for 'filter_type'. "
#                                     f"Valid values: ['column_value', 'search_text'].",
#                                     f"'wrong_param' is invalid value for 'comparison'. "
#                                     f"Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."}
#
#
# def test_wrong__model_class__filter_type__column(fake_session):
#     data = {"model_class": "wrong_param",
#             "filter_type": "wrong_param",
#             "comparison": "is",
#             "column": "wrong_param",
#             "column_value": "test_filter_1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {
#         f"'wrong_param' is invalid value for 'model_class'. "
#         f"Valid values: [<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
#         f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
#         f'\'wrong_param\' is invalid value for \'column\'. Valid values: '
#         f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
#         f'"for <class \'app.models.Advertisement\'>": '
#         f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'
#     }
#
#
# @pytest.mark.parametrize("column", ("name", "title"))
# def test_wrong__model_class__filter_type__column_value(fake_session, column):
#     data = {"model_class": "wrong_param",
#             "filter_type": "wrong_param",
#             "comparison": "is",
#             "column": column,
#             "column_value": "wrong_param"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {
#         f"'wrong_param' is invalid value for 'model_class'. "
#         f"Valid values: [<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
#         f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
#     }
#
#
# @pytest.mark.parametrize("column", ("name", "title"))
# def test_wrong__model_class__comparison__column_value(fake_session, column):
#     data = {"model_class": "wrong_param",
#             "filter_type": "column_value",
#             "comparison": "wrong_param",
#             "column": column,
#             "column_value": "wrong_param"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {
#         f"'wrong_param' is invalid value for 'model_class'. Valid values: "
#         f"[<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
#         f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."
#     }
#
#
# def test_wrong__model_class__column__column_value(fake_session):
#     data = {"model_class": "wrong_param",
#             "filter_type": "column_value",
#             "comparison": "is",
#             "column": "wrong_param",
#             "column_value": "wrong_param"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {
#         f"'wrong_param' is invalid value for 'model_class'. "
#         f"Valid values: [<class 'app.models.User'>, <class 'app.models.Advertisement'>].",
#         f'\'wrong_param\' is invalid value for \'column\'. Valid values: '
#         f'{{"for <class \'app.models.User\'>": [\'id\', \'name\', \'email\', \'creation_date\'], '
#         f'"for <class \'app.models.Advertisement\'>": '
#         f'[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\']}}.'
#     }
#
#
# @pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
# def test_wrong__filter_type__comparison__column_value(fake_session, model_class, column):
#     data = {"model_class": model_class,
#             "filter_type": "wrong_param",
#             "comparison": "wrong_param",
#             "column": column,
#             "column_value": "wrong_param"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {
#         f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
#         f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<=']."
#     }
#
#
# @pytest.mark.parametrize("model_class,columns",
#                          ((User, ['id', 'name', 'email', 'creation_date']),
#                           (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
# def test_wrong__filter_type__column__column_value(fake_session, model_class, columns):
#     data = {"model_class": model_class,
#             "filter_type": "wrong_param",
#             "comparison": "is",
#             "column": "wrong_param",
#             "column_value": "wrong_param"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {
#         f"'wrong_param' is invalid value for 'filter_type'. Valid values: ['column_value', 'search_text'].",
#         f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."
#     }
#
#
# @pytest.mark.parametrize("model_class,columns",
#                          ((User, ['id', 'name', 'email', 'creation_date']),
#                           (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
# def test_wrong__comparison__column__column_value(fake_session, model_class, columns):
#     data = {"model_class": model_class,
#             "filter_type": "column_value",
#             "comparison": "wrong_param",
#             "column": "wrong_param",
#             "column_value": "wrong_param"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {
#         f"'wrong_param' is invalid value for 'comparison'. Valid values: ['is', 'is_not', '<', '>', '>=', '<='].",
#         f"'wrong_param' is invalid value for 'column'. Valid values: {columns}."
#     }
#
#
# @pytest.mark.parametrize("model_class,column", ((User, 'id'), (Advertisement, 'id'), (Advertisement, 'user_id')))
# def test_nondigit_characters_as__id__user_id(fake_session, model_class, column):
#     data = {"model_class": model_class,
#             "filter_type": "column_value",
#             "comparison": "is",
#             "column": column,
#             "column_value": "wrong_param"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"'{column}' must be a digit."}
#
#
# @pytest.mark.parametrize("model_class,wrong_date", ((User, "non_date_value"),
#                                                     (Advertisement, "non_date_value"),
#                                                     (User, 2024),
#                                                     (Advertisement, 2024),
#                                                     (User, "01/01/2024"),
#                                                     (Advertisement, "01/01/2024")))
# def test_wrong_data_format_as__creation_date(fake_session, model_class, wrong_date):
#     data = {"model_class": model_class,
#             "filter_type": "column_value",
#             "comparison": "is",
#             "column": "creation_date",
#             "column_value": wrong_date}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {f"When column='creation_date', 'column_value' must be a date "
#                                     f"string of the following format: 'YYYY-MM-DD'."}
#
#
# @pytest.mark.parametrize("model_class,comparison,column", ((User, ">", "name"),
#                                                            (User, ">=", "name"),
#                                                            (User, "<", "name"),
#                                                            (User, "<=", "name"),
#                                                            (User, ">", "email"),
#                                                            (User, ">=", "email"),
#                                                            (User, "<", "email"),
#                                                            (User, "<=", "email"),
#                                                            (Advertisement, ">", "title"),
#                                                            (Advertisement, ">=", "title"),
#                                                            (Advertisement, "<", "title"),
#                                                            (Advertisement, "<=", "title"),
#                                                            (Advertisement, ">", "description"),
#                                                            (Advertisement, ">=", "description"),
#                                                            (Advertisement, "<", "description"),
#                                                            (Advertisement, "<=", "description")))
# def test_wrong_comparison_for_text_fields(fake_session, model_class, comparison, column):
#     data = {"model_class": model_class,
#             "filter_type": "column_value",
#             "comparison": comparison,
#             "column": column,
#             "column_value": "test_filter_1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {
#         f"'{comparison}' is invalid value for 'comparison'. Valid values: ['is', 'is_not']."
#     }
#
#
# @pytest.mark.parametrize("model_class,column", ((User, "id"), (Advertisement, "id"), (Advertisement, "user_id")))
# def test_unexpected_columns_with__search_text__filter_type(fake_session, model_class, column):
#     data = {"model_class": model_class,
#             "filter_type": "search_text",
#             "comparison": "",
#             "column": column,
#             "column_value": "1000"}
#     filter_object = Filter(session=fake_session)
#     filter_object.validate_params(data=data, params=Params)
#     assert filter_object.errors == {
#         "For filter_type='search_text' the folowing columns are available: "
#         "{for <class 'app.models.User'>: [name, email], for <class 'app.models.Advertisement'>: [title, description]}"
#     }
