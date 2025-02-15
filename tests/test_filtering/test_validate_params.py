import pytest

import app.domain.errors
from app.repository.filtering import Filter, Params, ValidParams
from app.domain.models import Advertisement, User


def test_validate_params_does_not_raise_validation_error_when_all_params_are_correct():
    data = {"model_class": Advertisement, "filter_type": "column_value", "comparison": ">=", "column": "id",
            "column_value": "1000"}
    filter_instance = Filter("fake_session")
    filter_instance._validate_params(data=data, params=Params)
    assert filter_instance.params_info.logs == set()
    assert filter_instance.params_info.missing_params == []
    assert filter_instance.params_info.invalid_params == {}


@pytest.mark.parametrize(
    "data",
    (
            {"model_class": "INVALID", "filter_type": "INVALID", "column": "INVALID", "column_value": "INVALID",
             "comparison": "INVALID"},
            {"model_class": "", "filter_type": "", "comparison": "", "column": "", "column_value": ""},
    )
)
def test_validate_params_raises_validation_error_when_all_params_are_invalid(data):
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {'model_class', 'filter_type', 'column', 'comparison'}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["model_class"]) == set(
        "Valid values are: [<class 'app.models.User'>, " f"<class 'app.models.Advertisement'>]"
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


def test_validate_params_raises_validation_error_when_all_params_are_missing():
    data = {}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "missing_params"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["missing_params"]) == {
        'model_class', 'filter_type', 'column', 'column_value', 'comparison'
    }


def test_validate_params_raises_validation_error_when_all_params_are_none():
    data = {"model_class": None, "filter_type": None, "comparison": None, "column": None, "column_value": None}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "missing_params"}
    assert e.value.message["params_passed"] == {}
    assert set(e.value.message["missing_params"]) == {
        'model_class', 'filter_type', 'column', 'column_value', 'comparison'
    }


def test_validate_params_raises_validation_error_when_filter_type_and_comparison_are_missing():
    data = {"model_class": User, "column": "id", "column_value": "text"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "missing_params"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["missing_params"]) == {'filter_type', 'comparison'}


def test_validate_params_raises_validation_error_when_model_class_is_invalid():
    data = {"model_class": "INVALID", "filter_type": "column_value", "comparison": "is", "column": "name",
            "column_value": "test"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"model_class"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["model_class"]) == set(
        f"Valid values are: {ValidParams.MODEL_CLASS.value}"
    )


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_validate_params_raises_validation_error_when_filter_type_is_invalid(model_class, column):
    data = {"model_class": model_class, "filter_type": "INVALID", "comparison": "is", "column": column,
            "column_value": "test"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"filter_type"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["filter_type"]) == set(
        "Valid values are: ['column_value', 'search_text']"
    )


def test_validate_params_raises_validation_error_when_model_class_and_filter_type_are_invalid():
    data = {"model_class": "INVALID", "filter_type": "INVALID", "comparison": "is", "column": "name",
            "column_value": "test"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"model_class", "filter_type"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["model_class"]) == set(
        "Valid values are: [<class 'app.models.User'>, <class 'app.models.Advertisement'>]"
    )
    assert set(e.value.message["invalid_params"]["filter_type"]) == set(
        "Valid values are: ['column_value', 'search_text']"
    )


@pytest.mark.parametrize(
    "model_class,columns",
    (
            (User, ['id', 'name', 'email', 'creation_date']),
            (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id']),
    )
)
def test_validate_params_raises_validation_error_when_column_is_invalid(model_class, columns):
    data = {"model_class": model_class, "filter_type": "column_value", "comparison": "is", "column": "INVALID",
            "column_value": "test"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"column"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["column"]) == set(
        f'For model class "{model_class.__name__}" valid values for "column" are: {columns}.'
    )


@pytest.mark.parametrize(
    "model_class,columns",
    (
            (User, ['id', 'name', 'email', 'creation_date']),
            (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id']),
    )
)
def test_validate_params_raises_validation_error_when_filter_type_and_column_are_invalid(model_class, columns):
    data = {"model_class": model_class, "filter_type": "INVALID", "comparison": "is", "column": "INVALID",
            "column_value": "test"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"filter_type", "column"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["filter_type"]) == set(
        "Valid values are: ['column_value', 'search_text']"
    )
    assert set(e.value.message["invalid_params"]["column"]) == set(
        f'For model class "{model_class.__name__}" valid values for "column" are: {columns}.'
    )


def test_validate_params_raises_validation_error_when_model_class_and_column_are_invalid():
    data = {"model_class": "INVALID", "filter_type": "column_value", "comparison": "is", "column": "INVALID",
            "column_value": "test"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"model_class", "column"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["model_class"]) == set(
        "Valid values are: [<class 'app.models.User'>, <class 'app.models.Advertisement'>]"
    )
    assert set(e.value.message["invalid_params"]["column"]) == set(
        "Valid values are: ['description', 'creation_date', 'user_id', 'name', 'email', 'id', 'title']"
    )


def test_validate_params_raises_validation_error_when_column_for_model_class_adv_is_wrong_and_filter_type_missing():
    data = {"model_class": Advertisement, "column": "wrong", "column_value": "2025-01-01", "comparison": "is"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "missing_params", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"column"}
    assert e.value.message["params_passed"] == data
    assert e.value.message["missing_params"] == ['filter_type']
    assert e.value.message["invalid_params"]["column"] == \
           'For model class "Advertisement" valid values for "column" are: ' \
           '[\'id\', \'title\', \'description\', \'creation_date\', \'user_id\'].'


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_validate_params_raises_validation_error_when_comparison_is_invalid(model_class, column):
    data = {"model_class": model_class, "filter_type": "column_value", "comparison": "INVALID", "column": column,
            "column_value": "test"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter(session="fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"comparison"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["comparison"]) == set(
        "Valid values are: ['is', 'is_not', '<', '>', '>=', '<=']"
    )


@pytest.mark.parametrize(
    "model_class,columns",
    (
            (User, ['id', 'name', 'email', 'creation_date']),
            (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id']),
    )
)
def test_validate_params_raises_validation_error_when_comparison_and_column_are_invalid(model_class, columns):
    data = {"model_class": model_class, "filter_type": "column_value", "comparison": "INVALID",
            "column": "INVALID", "column_value": "test"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"column", "comparison"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["column"]) == set(
        f'For model class "{model_class.__name__}" valid values for "column" are: {columns}.'
    )
    assert set(e.value.message["invalid_params"]["comparison"]) == set(
        "Valid values are: ['is', 'is_not', '<', '>', '>=', '<=']"
    )


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_validate_params_raises_validation_error_when_filter_type_and_comparison_are_invalid(model_class, column):
    data = {"model_class": model_class, "filter_type": "INVALID", "comparison": "INVALID", "column": column,
            "column_value": "test"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"filter_type", "comparison"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["filter_type"]) == set(
        "Valid values are: ['column_value', 'search_text']"
    )
    assert set(e.value.message["invalid_params"]["comparison"]) == set(
        "Valid values are: ['is', 'is_not', '<', '>', '>=', '<=']"
    )


def test_validate_params_raises_validation_error_when_model_class_and_comparison_are_invalid():
    data = {"model_class": "INVALID", "filter_type": "column_value", "comparison": "INVALID", "column": "name",
            "column_value": "test"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"model_class", "comparison"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["model_class"]) == set(
        "Valid values are: [<class 'app.models.User'>, <class 'app.models.Advertisement'>]"
    )
    assert set(e.value.message["invalid_params"]["comparison"]) == set(
        "Valid values are: ['is', 'is_not', '<', '>', '>=', '<=']"
    )


@pytest.mark.parametrize("column", ("name", "title"))
def test_validate_params_raises_validation_error_when_model_class_filter_type_and_comparison_are_invalid(column):
    data = {"model_class": "INVALID", "filter_type": "INVALID", "comparison": "INVALID", "column": column,
            "column_value": "test"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"model_class", "filter_type", "comparison"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["model_class"]) == set(
        "Valid values are: [<class 'app.models.User'>, <class 'app.models.Advertisement'>]"
    )
    assert set(e.value.message["invalid_params"]["filter_type"]) == set(
        "Valid values are: ['column_value', 'search_text']"
    )
    assert set(e.value.message["invalid_params"]["comparison"]) == set(
        "Valid values are: ['is', 'is_not', '<', '>', '>=', '<=']"
    )


@pytest.mark.parametrize(
    "model_class,comparison,column",
    (
            (User, ">", "name"),
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
            (Advertisement, "<=", "description"),
    )
)
def test_validate_params_raises_error_when_ft_is_column_value_column_is_a_text_field_and_comparison_is_unexpacted(
        model_class, comparison, column
):
    data = {"model_class": model_class, "filter_type": "column_value", "comparison": comparison, "column": column,
            "column_value": "3"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"comparison"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["comparison"]) == set(
        f'When "filter_type" is "column_value" and "column" is "{column}", valid values for "comparison" are: '
        f'[\'is\', \'is_not\'].'
    )


@pytest.mark.parametrize(
    "model_class,wrong_date", (
            (User, "non_date_value"),
            (Advertisement, "non_date_value"),
            (User, 2024),
            (Advertisement, 2024),
            (User, "01/01/2024"),
            (Advertisement, "01/01/2024")
    )
)
def test_validate_params_raises_validation_error_when_column_is_creation_date_and_column_value_is_a_wrong_date(
        model_class, wrong_date
):
    data = {"model_class": model_class, "filter_type": "column_value", "comparison": "is", "column": "creation_date",
            "column_value": wrong_date}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"column_value"}
    assert e.value.message["params_passed"] == data
    assert e.value.message["invalid_params"]["column_value"] == \
           'When "column" is "creation_date", "column_value" must be a date string of the following format: ' \
           '"YYYY-MM-DD".'


@pytest.mark.parametrize("model_class,column", ((User, 'id'), (Advertisement, 'id'), (Advertisement, 'user_id')))
def test_validate_params_raises_validation_error_when_column_is_id_or_user_id_and_column_value_is_nondigit_characters(
        model_class, column
):
    data = {"model_class": model_class, "filter_type": "column_value", "comparison": "is", "column": column,
            "column_value": "INVALID"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"column_value"}
    assert e.value.message["params_passed"] == data
    assert e.value.message["invalid_params"]["column_value"] == \
           f'When "column" is "{column}", "column_value" must be a digit.'


@pytest.mark.parametrize(
    "data",
    (
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


@pytest.mark.parametrize(
    "model_class,column,available_columns",
    (
            (User, "id", ["name", "email"]),
            (User, "creation_date", ["name", "email"]),
            (Advertisement, "id", ["title", "description"]),
            (Advertisement, "user_id", ["title", "description"]),
            (Advertisement, "creation_date", ["title", "description"]),
    )
)
def test_validate_params_raises_validation_error_when_filter_type_is_search_text_and_column_is_unexpected(
        model_class, column, available_columns
):
    data = {"model_class": model_class, "filter_type": "search_text", "comparison": "", "column": column,
            "column_value": "test"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"column"}
    assert e.value.message["params_passed"] == data
    assert e.value.message["invalid_params"]["column"] == \
           f'For model class "{model_class.__name__}" text search is available in the following columns: ' \
           f'{available_columns}.'


def test_validate_params_raises_validation_error_when_model_class_filter_type_and_column_are_invalid():
    data = {"model_class": "INVALID", "filter_type": "INVALID", "comparison": "is", "column": "INVALID",
            "column_value": "test"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"model_class", "filter_type", "column"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["model_class"]) == set(
        "Valid values are: [<class 'app.models.User'>, <class 'app.models.Advertisement'>]"
    )
    assert set(e.value.message["invalid_params"]["filter_type"]) == set(
        "Valid values are: ['column_value', 'search_text']"
    )
    assert set(e.value.message["invalid_params"]["column"]) == set(
        "Valid values are: ['id', 'title', 'creation_date', 'name', 'user_id', 'email', 'description']"
    )


@pytest.mark.parametrize("column", ("name", "title"))
def test_validate_params_raises_validation_error_when_model_class_filter_type_and_column_value_are_invalid(column):
    data = {"model_class": "INVALID", "filter_type": "INVALID", "comparison": "is", "column": column,
            "column_value": "INVALID"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"model_class", "filter_type"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["model_class"]) == set(
        "Valid values are: [<class 'app.models.User'>, <class 'app.models.Advertisement'>]"
    )
    assert set(e.value.message["invalid_params"]["filter_type"]) == set(
        "Valid values are: ['column_value', 'search_text']"
    )


@pytest.mark.parametrize("column", ("name", "title"))
def test_validate_params_raises_validation_error_when_model_class_comparison_and_column_value_are_invalid(column):
    data = {"model_class": "INVALID", "filter_type": "column_value", "comparison": "INVALID", "column": column,
            "column_value": "INVALID"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"model_class", "comparison"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["model_class"]) == set(
        "Valid values are: [<class 'app.models.User'>, <class 'app.models.Advertisement'>]"
    )
    assert set(e.value.message["invalid_params"]["comparison"]) == set(
        "Valid values are: ['is', 'is_not', '<', '>', '>=', '<=']"
    )


def test_validate_params_raises_validation_error_when_model_class_column_and_column_value_are_invalid():
    data = {"model_class": "INVALID", "filter_type": "column_value", "comparison": "is", "column": "INVALID",
            "column_value": "INVALID"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"model_class", "column"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["model_class"]) == set(
        "Valid values are: [<class 'app.models.User'>, <class 'app.models.Advertisement'>]"
    )
    assert set(e.value.message["invalid_params"]["column"]) == set(
        "Valid values are: ['description', 'creation_date', 'user_id', 'name', 'email', 'id', 'title']"
    )


@pytest.mark.parametrize("model_class,column", ((User, "name"), (Advertisement, "title")))
def test_validate_params_raises_validation_error_when_filter_type_comparison_and_column_value_are_invalid(
        model_class, column
):
    data = {"model_class": model_class, "filter_type": "INVALID", "comparison": "INVALID", "column": column,
            "column_value": "INVALID"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"filter_type", "comparison"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["filter_type"]) == set(
        "Valid values are: ['column_value', 'search_text']"
    )
    assert set(e.value.message["invalid_params"]["comparison"]) == set(
        "Valid values are: ['is', 'is_not', '<', '>', '>=', '<=']"
    )


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_validate_params_raises_validation_error_when_filter_type_column_and_column_value_are_invalid(
        model_class, columns
):
    data = {"model_class": model_class, "filter_type": "INVALID", "comparison": "is", "column": "INVALID",
            "column_value": "INVALID"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"filter_type", "column"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["filter_type"]) == set(
        "Valid values are: ['column_value', 'search_text']"
    )


@pytest.mark.parametrize("model_class,columns",
                         ((User, ['id', 'name', 'email', 'creation_date']),
                          (Advertisement, ['id', 'title', 'description', 'creation_date', 'user_id'])))
def test_validate_params_raises_validation_error_when_comparison_column_column_value_are_invalid(
        model_class, columns
):
    data = {"model_class": model_class, "filter_type": "column_value", "comparison": "INVALID", "column": "INVALID",
            "column_value": "INVALID"}
    with pytest.raises(app.domain.errors.ValidationError) as e:
        Filter("fake_session")._validate_params(data=data, params=Params)
    assert set(e.value.message.keys()) == {"params_passed", "invalid_params"}
    assert set(e.value.message["invalid_params"].keys()) == {"comparison", "column"}
    assert e.value.message["params_passed"] == data
    assert set(e.value.message["invalid_params"]["column"]) == set(
        f'For model class "{model_class.__name__}" valid values for "column" are: {columns}.'
    )
    assert set(e.value.message["invalid_params"]["comparison"]) == set(
        "Valid values are: ['is', 'is_not', '<', '>', '>=', '<=']"
    )


