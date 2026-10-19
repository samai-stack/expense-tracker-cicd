import pytest

from app.models import Expense, ValidationError, parse_amount, validate_expense


def make(**overrides):
    data = {"amount": "1500", "category": "food", "description": "Обед", "spent_on": "2026-10-01"}
    data.update(overrides)
    return validate_expense(data)


def test_valid_expense():
    expense = make()
    assert expense.amount == 1500.0
    assert expense.category == "food"
    assert expense.spent_on == "2026-10-01"


@pytest.mark.parametrize(("raw", "expected"), [("10", 10.0), (2.345, 2.35), ("0.01", 0.01)])
def test_parse_amount_rounds_to_cents(raw, expected):
    assert parse_amount(raw) == expected


@pytest.mark.parametrize("raw", ["abc", None, "0", "-5", "nan", "inf", "100000000"])
def test_parse_amount_rejects_bad_values(raw):
    with pytest.raises(ValidationError):
        parse_amount(raw)


def test_category_is_normalized():
    assert make(category="  Transport ").category == "transport"


def test_unknown_category_rejected():
    with pytest.raises(ValidationError, match="категория"):
        make(category="casino")


def test_long_description_rejected():
    with pytest.raises(ValidationError):
        make(description="x" * 201)


def test_bad_date_rejected():
    with pytest.raises(ValidationError, match="ГГГГ-ММ-ДД"):
        make(spent_on="01.10.2026")


def test_missing_date_defaults_to_today():
    assert make(spent_on="").spent_on


def test_non_dict_rejected():
    with pytest.raises(ValidationError):
        validate_expense(None)


def test_store_add_get_delete(store):
    saved = store.add(make())
    assert saved.id is not None
    assert store.get(saved.id) == saved
    assert store.delete(saved.id) is True
    assert store.get(saved.id) is None
    assert store.delete(saved.id) is False


def test_store_filters_and_summary(store):
    store.add(make(amount="1000", category="food", spent_on="2026-10-02"))
    store.add(make(amount="500", category="food", spent_on="2026-10-05"))
    store.add(make(amount="2000", category="transport", spent_on="2026-09-30"))

    assert len(store.list()) == 3
    assert [e.amount for e in store.list(category="food")] == [500.0, 1000.0]
    assert len(store.list(month="2026-10")) == 2

    summary = store.summary()
    assert summary["count"] == 3
    assert summary["total"] == 3500.0
    assert list(summary["by_category"]) == ["transport", "food"]
    assert store.summary(month="2026-09")["total"] == 2000.0


def test_expense_to_dict():
    expense = Expense(id=1, amount=5.0, category="other", description="", spent_on="2026-01-01")
    assert expense.to_dict()["category"] == "other"
