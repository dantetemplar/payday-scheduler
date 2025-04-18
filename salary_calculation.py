from datetime import date, datetime, timedelta
from typing import Literal, TypedDict, assert_never

import requests
import streamlit as st


class Month(TypedDict):
    id: int
    name: str
    workingDays: int
    notWorkingDays: int
    shortDays: int
    workingHours: int


class SalaryResult(TypedDict):
    before_tax: float
    tax: float
    after_tax: float


class Holiday(TypedDict):
    date: date
    name: str


class HolidaysData(TypedDict):
    year: int
    holidays: list[Holiday]
    shortDays: list[Holiday]


class PaydayScheduleItem(TypedDict):
    date: date
    it_is: Literal["advance", "salary"]
    working_days: int
    max_working_days: int
    salary: SalaryResult
    date_was_moved: bool


@st.cache_data
def get_work_calendar(year: int) -> dict[int, Month]:
    """Get work calendar for a given year.

    Args:
        year: The year to get the calendar for

    Returns:
        A dictionary where keys are month numbers (1-12)
        and values are dictionaries containing all month data:
        - name: Month name
        - workingDays: Number of working days
        - notWorkingDays: Number of non-working days
        - shortDays: Number of short days
        - workingHours: Total working hours
    """
    response = requests.get(f"https://calendar.kuzyak.in/api/calendar/{year}")
    response.raise_for_status()
    calendar_data = response.json()

    months_data: dict[int, Month] = {}
    for month in calendar_data["months"]:
        # API returns months with id 0-11, we need 1-12
        months_data[month["id"] + 1] = {
            "id": month["id"] + 1,
            "name": month["name"],
            "workingDays": month["workingDays"],
            "notWorkingDays": month["notWorkingDays"],
            "shortDays": month["shortDays"],
            "workingHours": month["workingHours"],
        }

    return months_data


@st.cache_data
def get_holidays_and_short_days(year: int) -> HolidaysData:
    """Get holidays and short days for a given year.

    Args:
        year: The year to get the data for

    Returns:
        A dictionary containing:
        - year: The year
        - holidays: List of holidays with dates and names
        - shortDays: List of short days with dates and names
    """
    response = requests.get(f"https://calendar.kuzyak.in/api/calendar/{year}/holidays")
    response.raise_for_status()
    raw_data = response.json()

    # Convert date strings to datetime.date objects
    holidays_data = {
        "year": raw_data["year"],
        "holidays": [
            {"date": datetime.fromisoformat(h["date"].replace("Z", "+00:00")).date(), "name": h["name"]}
            for h in raw_data["holidays"]
        ],
        "shortDays": [
            {"date": datetime.fromisoformat(h["date"].replace("Z", "+00:00")).date(), "name": h["name"]}
            for h in raw_data["shortDays"]
        ],
    }

    return HolidaysData(**holidays_data)


def calculate_salary(
    month: int,
    year: int,
    days_worked: int,
    amount: float,
    mode: Literal["До вычета НДФЛ", "На руки"] = "До вычета НДФЛ",
) -> SalaryResult:
    """Calculate salary for a given month.

    Args:
        month: Month number (1-12)
        year: Year number (e.g. 2024)
        days_worked: Number of days worked in the month
        amount: Amount specified (either before or after tax)
        mode: Either "До вычета НДФЛ" or "На руки"

    Returns:
        Dictionary containing:
        - before_tax: Amount before tax
        - tax: Tax amount (NDFL)
        - after_tax: Amount after tax
    """
    TAX_RATE = 0.13

    calendar = get_work_calendar(year)
    work_days = calendar[month]["workingDays"]
    daily_rate = amount / work_days
    period_amount = daily_rate * days_worked

    if mode == "До вычета НДФЛ":
        before_tax = period_amount
        tax = before_tax * TAX_RATE
        after_tax = before_tax - tax
    elif mode == "На руки":
        after_tax = period_amount
        # If we want X after tax, then X = Y - Y*0.13 where Y is before tax
        # Solving for Y: X = Y(1-0.13) => Y = X/(1-0.13)
        before_tax = after_tax / (1 - TAX_RATE)
        tax = before_tax * TAX_RATE
    else:
        assert_never(mode)

    return {"before_tax": before_tax, "tax": tax, "after_tax": after_tax}


def get_previous_working_day(date: date, holidays_data: HolidaysData) -> date:
    """Find the previous working day that is not a holiday or weekend.

    Args:
        date: The date to start checking from
        holidays_data: Holidays and short days data

    Returns:
        The previous working day
    """
    current_date = date
    while True:
        # Check if it's a holiday
        is_holiday = any(h["date"] == current_date for h in holidays_data["holidays"])
        # Check if it's a weekend (5=Saturday, 6=Sunday)
        is_weekend = current_date.weekday() >= 5

        if not is_holiday and not is_weekend:
            return current_date

        current_date -= timedelta(days=1)


def get_payday_schedule(
    year: int,
    advance_day: int,
    mode: Literal["До вычета НДФЛ", "На руки"] = "До вычета НДФЛ",
    amount: float = 0.0,
    working_days: list[tuple[int, int]] | None = None,
) -> list[PaydayScheduleItem]:
    """Generate a schedule of paydays for a given year.

    Args:
        year: The year to generate the schedule for
        advance_day: Day of the month for advance payment
        mode: Either "До вычета НДФЛ" or "На руки"
        amount: The salary amount (either before or after tax depending on mode)
        working_days: Optional list of tuples (advance_working_days, salary_working_days) for each month.
            If not provided, working days will be calculated automatically:
            - advance: all working days in first half of month
            - salary: remaining working days in month

    Returns:
        A list of payday schedule items containing:
        - date: The payment date
        - it_is: Either "advance" or "salary"
        - working_days: Number of working days in the period
        - salary: Salary calculation result
    """
    schedule: list[PaydayScheduleItem] = []
    calendar = get_work_calendar(year)
    holidays_data = get_holidays_and_short_days(year)

    if working_days is not None and len(working_days) != 12:
        raise ValueError("working_days must contain exactly 12 tuples (one for each month)")

    for month in range(1, 13):
        # Calculate advance payment date
        # Handle months with fewer days than advance_day
        last_day_of_month = (date(year, month + 1, 1) - timedelta(days=1)).day if month < 12 else 31
        actual_advance_day = min(advance_day, last_day_of_month)
        original_advance_date = date(year, month, actual_advance_day)
        advance_date = get_previous_working_day(original_advance_date, holidays_data)
        advance_date_was_moved = advance_date != original_advance_date

        # Calculate salary payment date (next month)
        salary_day = advance_day - 15
        if salary_day < 1:
            salary_day = 1
        salary_month = month + 1
        salary_year = year
        if salary_month > 12:
            salary_month = 1
            salary_year = year + 1

        # Handle months with fewer days than salary_day
        last_day_of_salary_month = (
            (date(salary_year, salary_month + 1, 1) - timedelta(days=1)).day if salary_month < 12 else 31
        )
        actual_salary_day = min(salary_day, last_day_of_salary_month)
        original_salary_date = date(salary_year, salary_month, actual_salary_day)
        salary_date = get_previous_working_day(original_salary_date, holidays_data)
        salary_date_was_moved = salary_date != original_salary_date

        # Count working days in first half of month
        first_day = date(year, month, 1)
        last_day = date(year, month, 15)
        current_day = first_day
        max_advance_working_days = 0

        while current_day <= last_day:
            # Check if it's a holiday or weekend
            is_holiday = any(h["date"] == current_day for h in holidays_data["holidays"])
            is_weekend = current_day.weekday() >= 5  # 5 is Saturday, 6 is Sunday

            if not is_holiday and not is_weekend:
                max_advance_working_days += 1

            current_day += timedelta(days=1)

        # For salary: remaining working days in month
        max_salary_working_days = calendar[month]["workingDays"] - max_advance_working_days

        # Calculate working days for each period
        if working_days is not None:
            advance_working_days, salary_working_days = working_days[month - 1]
            if advance_working_days + salary_working_days > calendar[month]["workingDays"]:
                raise ValueError(
                    f"Total working days for month {month} ({advance_working_days + salary_working_days}) "
                    f"exceeds calendar working days ({calendar[month]['workingDays']})"
                )
        else:
            advance_working_days = max_advance_working_days
            salary_working_days = max_salary_working_days

        # Calculate salary for each period
        advance_salary = calculate_salary(month, year, advance_working_days, amount, mode)
        salary_salary = calculate_salary(month, year, salary_working_days, amount, mode)

        # Add to schedule
        schedule.append(
            {
                "date": advance_date,
                "it_is": "advance",
                "working_days": advance_working_days,
                "max_working_days": max_advance_working_days,
                "salary": advance_salary,
                "date_was_moved": advance_date_was_moved,
            }
        )

        schedule.append(
            {
                "date": salary_date,
                "it_is": "salary",
                "working_days": salary_working_days,
                "max_working_days": max_salary_working_days,
                "salary": salary_salary,
                "date_was_moved": salary_date_was_moved,
            }
        )

    return schedule


@st.cache_data
def get_usd_rate() -> float:
    """Get current USD exchange rate from Central Bank of Russia.

    Returns:
        Current USD exchange rate in RUB
    """
    try:
        response = requests.get("https://www.cbr-xml-daily.ru/daily_json.js")
        response.raise_for_status()
        data = response.json()
        return float(data["Valute"]["USD"]["Value"])
    except Exception as e:
        # Fallback to a reasonable rate if API fails
        print(f"Failed to fetch USD rate: {e}")
        return 90.0  # Fallback rate
