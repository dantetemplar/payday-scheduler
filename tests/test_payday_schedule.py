from datetime import date

import pytest


def test_get_payday_schedule_basic():
    """Test basic functionality of get_payday_schedule."""
    from salary_calculation import get_payday_schedule

    # Test with January 2025, advance on 25th, salary on 10th next month, 60k salary before tax
    schedule = get_payday_schedule(2025, 25, "До вычета НДФЛ", 60000.0)

    # Should have 24 items (12 months * 2 payments)
    assert len(schedule) == 24

    # Check first month (January)
    for item in schedule:
        if item["date"] == date(2025, 1, 24):
            jan_advance = item
            break
    else:
        assert False, "Advance not found"

    assert jan_advance["it_is"] == "advance"
    assert jan_advance["working_days"] == 5  # January has 17 working days, but advance is only for first 5
    assert jan_advance["salary"]["before_tax"] == pytest.approx(17647, abs=1)
    assert jan_advance["salary"]["tax"] == pytest.approx(2294, abs=1)
    assert jan_advance["salary"]["after_tax"] == pytest.approx(15352, abs=1)

    for item in schedule:
        if item["date"] == date(2025, 2, 10):
            jan_salary = item
            break
    else:
        assert False, "Salary not found"

    assert jan_salary["it_is"] == "salary"
    assert jan_salary["working_days"] == 12
    assert jan_salary["salary"]["before_tax"] == pytest.approx(42352, abs=1)
    assert jan_salary["salary"]["tax"] == pytest.approx(5505, abs=1)
    assert jan_salary["salary"]["after_tax"] == pytest.approx(36847, abs=1)


def test_get_payday_schedule_net_mode():
    """Test get_payday_schedule with 'На руки' mode."""
    from salary_calculation import get_payday_schedule

    # Test with January 2025, advance on 25th, 60k salary after tax
    schedule = get_payday_schedule(2025, 25, "На руки", 60000.0)

    # Check first month (January)
    for item in schedule:
        if item["date"] == date(2025, 1, 24):  # 24 because 25th is a holiday
            jan_advance = item
            break
    else:
        assert False, "Advance not found"

    for item in schedule:
        if item["date"] == date(2025, 2, 10):
            jan_salary = item
            break
    else:
        assert False, "Salary not found"

    # sum up
    assert jan_advance["salary"]["before_tax"] + jan_salary["salary"]["before_tax"] == pytest.approx(68965, abs=1)
    assert jan_advance["salary"]["after_tax"] + jan_salary["salary"]["after_tax"] == pytest.approx(60000, abs=1)
    assert jan_advance["salary"]["tax"] + jan_salary["salary"]["tax"] == pytest.approx(8965, abs=1)


def test_get_payday_schedule_year_rollover():
    """Test that schedule correctly handles year rollover for December salary."""
    from salary_calculation import get_payday_schedule

    schedule = get_payday_schedule(2025, 25, "До вычета НДФЛ", 60000.0)

    # December salary should be paid in January 2026
    for item in schedule:
        if item["date"].year == 2026 and item["date"].month == 1:
            dec_salary = item
            break
    else:
        assert False, "Salary not found"

    assert dec_salary["it_is"] == "salary"
    assert dec_salary["working_days"] == 11  # December has 22 working days, 11 for advance, 11 for salary
