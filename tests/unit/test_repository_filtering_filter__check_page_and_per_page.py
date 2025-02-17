import pytest

from app.repository.filtering import Filter


class FakeQueryFiltered:
    def __init__(self, query_filtered):
        self.query_filtered = query_filtered

    def count(self):
        return self.query_filtered


def test_check_page_and_per_page_sets_page_to_self_page_default_value_when_page_passed_is_gt_self_query_filtered():
    page, per_page, fake_query_filtered = 5, 2, 1
    filter_object = Filter(session="fake_session")
    filter_object.query_filtered = FakeQueryFiltered(query_filtered=fake_query_filtered)
    result = filter_object._check_page_and_per_page(page=page, per_page=per_page)
    assert result == {"page": filter_object.page_default_value, "per_page": per_page}


@pytest.mark.parametrize("page,per_page,fake_query_filtered", ((3, 100, 5), (5, 100, 5)))
def test_check_page_and_per_page_sets_page_to_value_passed_when_value_passed_is_lt_or_et_self_query_filtered(
        page, per_page, fake_query_filtered
):
    filter_object = Filter(session="fake_session")
    filter_object.query_filtered = FakeQueryFiltered(query_filtered=fake_query_filtered)
    result = filter_object._check_page_and_per_page(page=page, per_page=per_page)
    assert result == {"page": page, "per_page": per_page}


def test_check_page_and_per_page_sets_page_and_per_page_to_default_values_when_invalid_values_are_passed():
    page, per_page, fake_query_filtered = "INVALID", "INVALID", 3
    filter_object = Filter(session="fake_session")
    filter_object.query_filtered = FakeQueryFiltered(query_filtered=fake_query_filtered)
    result = filter_object._check_page_and_per_page(page=page, per_page=per_page)
    assert result == {"page": filter_object.page_default_value, "per_page": filter_object.per_page_default_value}
