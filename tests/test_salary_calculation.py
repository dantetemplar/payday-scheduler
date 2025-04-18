from datetime import date

import pytest


def test_get_work_calendar():
    from salary_calculation import get_work_calendar

    """Test that work calendar is correctly generated for different years."""
    # Test 2025 calendar
    calendar_2025 = get_work_calendar(2025)

    # Basic validation
    assert len(calendar_2025) == 12, "Should have 12 months"
    assert all(isinstance(data, dict) for data in calendar_2025.values()), "All values should be dictionaries"
    assert all("workingDays" in data for data in calendar_2025.values()), "All month data should have workingDays"

    # Validation based on official work calendar for 2025
    assert calendar_2025[1]["workingDays"] == 17, "January 2025 should have 17 work days"
    assert calendar_2025[2]["workingDays"] == 20, "February 2025 should have 20 work days"
    assert calendar_2025[3]["workingDays"] == 21, "March 2025 should have 21 work days"
    assert calendar_2025[4]["workingDays"] == 22, "April 2025 should have 22 work days"
    assert calendar_2025[5]["workingDays"] == 18, "May 2025 should have 18 work days"
    assert calendar_2025[6]["workingDays"] == 19, "June 2025 should have 19 work days"
    assert calendar_2025[7]["workingDays"] == 23, "July 2025 should have 23 work days"
    assert calendar_2025[8]["workingDays"] == 21, "August 2025 should have 21 work days"
    assert calendar_2025[9]["workingDays"] == 22, "September 2025 should have 22 work days"
    assert calendar_2025[10]["workingDays"] == 23, "October 2025 should have 23 work days"
    assert calendar_2025[11]["workingDays"] == 19, "November 2025 should have 20 work days"
    assert calendar_2025[12]["workingDays"] == 22, "December 2025 should have 23 work days"

    # Test 2024 calendar
    calendar_2024 = get_work_calendar(2024)
    assert len(calendar_2024) == 12, "2024 calendar should have 12 months"
    assert all(isinstance(data, dict) for data in calendar_2024.values()), "All values should be dictionaries"
    assert all("workingDays" in data for data in calendar_2024.values()), "All month data should have workingDays"


def test_get_holidays_and_short_days():
    """Test that holidays and short days are correctly retrieved."""
    from salary_calculation import get_holidays_and_short_days

    # Test 2025 calendar
    holidays_2025 = get_holidays_and_short_days(2025)

    # Basic validation
    assert isinstance(holidays_2025, dict), "Should return a dictionary"
    assert "year" in holidays_2025, "Should have year field"
    assert "holidays" in holidays_2025, "Should have holidays field"
    assert "shortDays" in holidays_2025, "Should have shortDays field"

    # Check year
    assert holidays_2025["year"] == 2025, "Year should match requested year"

    # Check structure of holidays
    for holiday in holidays_2025["holidays"]:
        assert isinstance(holiday["date"], date), "Holiday date should be a date object"
        assert isinstance(holiday["name"], str), "Holiday name should be a string"
        assert len(holiday["name"]) > 0, "Holiday name should not be empty"

    # Check structure of short days
    for short_day in holidays_2025["shortDays"]:
        assert isinstance(short_day["date"], date), "Short day date should be a date object"
        assert isinstance(short_day["name"], str), "Short day name should be a string"
        assert len(short_day["name"]) > 0, "Short day name should not be empty"

    # Check New Year holidays from Jan 1-8
    new_year_dates = [date(2025, 1, d) for d in range(1, 9)]
    holiday_dates = [h["date"] for h in holidays_2025["holidays"]]

    for ny_date in new_year_dates:
        assert ny_date in holiday_dates, f"{ny_date} should be a holiday"


def test_calculate_salary():
    """Test salary calculation for different scenarios."""
    from salary_calculation import calculate_salary

    test_cases = [
        # (month, year, days_worked, Оклад до вычета НДФЛ, Выплата на руки)
        (1, 2025, 17, 60000, 52200.00),  # January 2025, full month
        (1, 2025, 15, 60000, 46058.83),  # January 2025, partial month
        (2, 2025, 20, 60000, 52200.00),  # February 2025, full month
        (2, 2025, 15, 60000, 39150.00),  # February 2025, partial month
    ]

    for month, year, days_worked, salary_before_tax, expected_salary in test_cases:
        result = calculate_salary(month, year, days_worked, salary_before_tax)
        assert result["after_tax"] == pytest.approx(
            expected_salary, abs=0.01
        ), f"Failed for month {month}, year {year}, days worked {days_worked}"

    # Test cases for "На руки" mode
    test_cases_net = [
        # (month, year, days_worked, Оклад на руки, Выплата до вычета НДФЛ)
        (1, 2025, 17, 60000.00, 68965.52),  # January 2025, full month
        (1, 2025, 15, 60000.00, 60851.93),  # January 2025, partial month
        (1, 2025, 2, 60000.00, 8113.59),  # January 2025, 2 days
        (2, 2025, 20, 60000.00, 68965.52),  # February 2025, full month
        (2, 2025, 15, 60000.00, 51724.14),  # February 2025, partial month
    ]

    for month, year, days_worked, net_salary, expected_salary in test_cases_net:
        result = calculate_salary(month, year, days_worked, net_salary, mode="На руки")
        assert result["before_tax"] == pytest.approx(
            expected_salary, abs=0.01
        ), f"Failed for month {month}, year {year}, days worked {days_worked}, mode=На руки"
