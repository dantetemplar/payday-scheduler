import locale
from datetime import datetime
from typing import Literal

import streamlit as st
from streamlit.components.v1 import html

from salary_calculation import calculate_salary, get_payday_schedule, get_usd_rate, get_work_calendar

# Constants
YEARS = [2023, 2024, 2025]
MONTH_NAMES = [
    "Январь",
    "Февраль",
    "Март",
    "Апрель",
    "Май",
    "Июнь",
    "Июль",
    "Август",
    "Сентябрь",
    "Октябрь",
    "Ноябрь",
    "Декабрь",
]

# Set Russian locale for number formatting
locale.setlocale(locale.LC_ALL, "ru_RU.UTF-8")


def format_currency(amount: float, currency: str = "₽") -> str:
    if currency == "$":
        return f"<span class='copyable-number' style='color: gray' data-copy='{amount:.2f}'>{amount:,.2f} {currency}</span>"
    return f"<span class='copyable-number' data-copy='{amount:.2f}'>{amount:,.2f} {currency}</span>"


def format_number_in_words(amount: float) -> str:
    # This is a simplified version - you might want to use a proper number-to-words library
    rubles = int(amount)
    kopecks = int((amount - rubles) * 100)
    return f"{rubles:,} рублей {kopecks:02d} копеек"


def get_nearest_year_index(years: list[int]) -> int:
    current_year = datetime.now().year
    return min(range(len(years)), key=lambda i: abs(years[i] - current_year))


st.set_page_config(page_title="Калькулятор зарплаты", layout="wide", page_icon=":dollar:")
st.sidebar.title("Навигация")

page = st.sidebar.radio(
    "Выберите раздел:", ["Посчитать зарплату", "Спланировать выплаты", "Производственный календарь"]
)
st.write(
    """
        <style>
        .copyable-number {
            cursor: pointer;
            transition: background-color 0.3s ease;
        }
        .copyable-number:hover {
            color: lime!important;
        }
        </style>
        """,
    unsafe_allow_html=True,
)

if page == "Посчитать зарплату":
    st.title("Калькулятор зарплаты")

    # Mode selection
    mode = st.radio("Режим расчета:", ["До вычета НДФЛ", "На руки"], key="salary_mode")
    mode_literal: Literal["До вычета НДФЛ", "На руки"] = mode  # type: ignore

    # Input fields
    col1, col2 = st.columns(2)

    with col2:
        current_date = datetime.now()
        month = st.selectbox("Месяц:", MONTH_NAMES, index=current_date.month - 1, key="salary_month")
        month_num = MONTH_NAMES.index(month) + 1  # Convert month name to number
        year = st.selectbox("Год:", YEARS, index=get_nearest_year_index(YEARS), key="salary_year")

    # Get total working days
    calendar = get_work_calendar(int(year))
    total_working_days = calendar[month_num]["workingDays"]

    with col1:
        if mode == "До вычета НДФЛ":
            amount = st.number_input("Размер оклада до вычета налога:", min_value=0.0, step=1000.0, key="salary_amount")
        else:
            amount = st.number_input("Размер оклада на руки:", min_value=0.0, step=1000.0, key="salary_amount")

        days_worked = st.number_input(
            f"отработано из {total_working_days} рабочих дней",
            min_value=0,
            max_value=total_working_days,
            value=total_working_days,
        )

    # Calculate salary
    result = calculate_salary(month_num, int(year), days_worked, amount, mode_literal)

    # Get USD rate
    usd_rate = get_usd_rate()
    st.markdown(f"**Курс доллара:** {format_currency(usd_rate)}", unsafe_allow_html=True)

    # Calculate annual salary
    annual_result = {"before_tax": 0.0, "tax": 0.0, "after_tax": 0.0}
    for month in range(1, 13):
        month_result = calculate_salary(month, int(year), calendar[month]["workingDays"], amount, mode_literal)
        annual_result["before_tax"] += month_result["before_tax"]
        annual_result["tax"] += month_result["tax"]
        annual_result["after_tax"] += month_result["after_tax"]

    # Display results
    st.markdown("---")
    st.subheader("Месячная зарплата")

    if mode == "До вычета НДФЛ":
        st.markdown(
            f"""<div style='line-height: 1.1;'>
<b>Сумма на руки:</b><br>
{format_currency(result['after_tax'])} {format_currency(result['after_tax'] / usd_rate, '$')}<br>
<br>
<b>Сумма НДФЛ, 13%:</b><br>
{format_currency(result['tax'])} {format_currency(result['tax'] / usd_rate, '$')}<br>
<br>
<b>Сумма до вычета НДФЛ:</b><br>
{format_currency(result['before_tax'])} {format_currency(result['before_tax'] / usd_rate, '$')}
</div>""",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""<div style='line-height: 1.1;'>
<b>Сумма до вычета НДФЛ:</b><br>
{format_currency(result['before_tax'])} {format_currency(result['before_tax'] / usd_rate, '$')}<br>
<br>
<b>Сумма НДФЛ, 13%:</b><br>
{format_currency(result['tax'])} {format_currency(result['tax'] / usd_rate, '$')}<br>
<br>
<b>Сумма на руки:</b><br>
{format_currency(result['after_tax'])} {format_currency(result['after_tax'] / usd_rate, '$')}
</div>""",
            unsafe_allow_html=True,
        )

    # Display annual salary
    st.markdown("---")
    st.subheader("Годовая зарплата")
    st.markdown(
        f"""<div style='line-height: 1.1;'>
<b>Сумма до вычета НДФЛ:</b><br>
{format_currency(annual_result['before_tax'])} {format_currency(annual_result['before_tax'] / usd_rate, '$')}<br>
<br>
<b>Сумма НДФЛ, 13%:</b><br>
{format_currency(annual_result['tax'])} {format_currency(annual_result['tax'] / usd_rate, '$')}<br>
<br>
<b>Сумма на руки:</b><br>
{format_currency(annual_result['after_tax'])} {format_currency(annual_result['after_tax'] / usd_rate, '$')}
</div>""",
        unsafe_allow_html=True,
    )


elif page == "Спланировать выплаты":
    st.title("Планирование выплат")

    # Add CSS for current month highlighting
    st.markdown(
        """
        <style>
        p:has(span.current-month) {
            color: lime;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        current_date = datetime.now()
        year = st.selectbox("Год:", YEARS, index=get_nearest_year_index(YEARS), key="payment_year")
        advance_day = st.number_input("День аванса:", min_value=16, max_value=31, value=16, key="payment_advance_day")

    with col2:
        mode = st.radio("Режим расчета:", ["До вычета НДФЛ", "На руки"], key="payment_mode")
        mode_literal: Literal["До вычета НДФЛ", "На руки"] = mode  # type: ignore
        amount = st.number_input("Размер оклада:", min_value=0.0, value=60000.0, step=1000.0, key="payment_amount")

    # Get payment schedule
    schedule = get_payday_schedule(int(year), advance_day, mode_literal, amount)

    # Display schedule
    st.markdown("---")
    st.subheader("График выплат")

    # Collect working days from all months
    working_days_list = []
    for i in range(0, len(schedule), 2):
        if i + 1 < len(schedule):  # Ensure we have both advance and salary
            advance = schedule[i]
            salary = schedule[i + 1]
            month_name = MONTH_NAMES[advance["date"].month - 1]
            # Get total working days for the month
            month_num = advance["date"].month
            calendar = get_work_calendar(int(year))
            total_working_days = calendar[month_num]["workingDays"]

            # Check if this is the current month
            is_current_month = month_num == current_date.month and int(year) == current_date.year

            if is_current_month:
                st.write(
                    f"**{month_name} {advance['date'].year}**, всего рабочих дней: {total_working_days} <span class='current-month'></span>",
                    unsafe_allow_html=True,
                )
            else:
                st.write(f"**{month_name} {advance['date'].year}**, всего рабочих дней: {total_working_days}")

            # Add working days input fields
            col1, col2 = st.columns(2)

            with col1:
                st.write("**Аванс**")
                col1a, col1b = st.columns([1, 3], vertical_alignment="center")
                with col1a:
                    advance_working_days = st.number_input(
                        "Рабочих дней",
                        min_value=0,
                        max_value=advance["max_working_days"],
                        value=advance["working_days"],
                        key=f"advance_days_{month_num}",
                        label_visibility="collapsed",
                    )
                with col1b:
                    st.write(f"из {advance['max_working_days']} рабочих дней")
                # Recalculate advance salary
                advance_salary = calculate_salary(month_num, int(year), advance_working_days, amount, mode_literal)
                st.markdown(
                    f"""<div style='line-height: 1.1;'>
<b>Дата:</b> {advance['date'].strftime('%d.%m.%Y')}<br>
<b>До вычета НДФЛ:</b> {format_currency(advance_salary['before_tax'])}<br>
<b>НДФЛ:</b> {format_currency(advance_salary['tax'])}<br>
<b>На руки:</b> {format_currency(advance_salary['after_tax'])}
</div>""",
                    unsafe_allow_html=True,
                )

            with col2:
                st.write("**Зарплата**")
                col2a, col2b = st.columns([1, 3], vertical_alignment="center")
                with col2a:
                    salary_working_days = st.number_input(
                        "Рабочих дней",
                        min_value=0,
                        max_value=salary["max_working_days"],
                        value=salary["working_days"],
                        key=f"salary_days_{month_num}",
                        label_visibility="collapsed",
                    )
                with col2b:
                    st.write(f"из {salary['max_working_days']} рабочих дней")
                # Recalculate salary
                salary_salary = calculate_salary(month_num, int(year), salary_working_days, amount, mode_literal)
                st.markdown(
                    f"""<div style='line-height: 1.1;'>
<b>Дата:</b> {salary['date'].strftime('%d.%m.%Y')}<br>
<b>До вычета НДФЛ:</b> {format_currency(salary_salary['before_tax'])}<br>
<b>НДФЛ:</b> {format_currency(salary_salary['tax'])}<br>
<b>На руки:</b> {format_currency(salary_salary['after_tax'])}
</div>""",
                    unsafe_allow_html=True,
                )

            # Add to working days list
            working_days_list.append((advance_working_days, salary_working_days))

            st.markdown("---")

    # Recalculate schedule with custom working days
    if working_days_list:
        schedule = get_payday_schedule(int(year), advance_day, mode_literal, amount, working_days=working_days_list)

else:  # Производственный календарь
    st.title("Производственный календарь")

    current_date = datetime.now()
    year = st.selectbox("Год:", YEARS, index=get_nearest_year_index(YEARS), key="calendar_year")

    calendar = get_work_calendar(int(year))

    for month_num, month_data in calendar.items():
        st.subheader(MONTH_NAMES[month_num - 1])
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.write("**Рабочих дней:**")
            st.write(month_data["workingDays"])

        with col2:
            st.write("**Выходных дней:**")
            st.write(month_data["notWorkingDays"])

        with col3:
            st.write("**Сокращенных дней:**")
            st.write(month_data["shortDays"])

        with col4:
            st.write("**Рабочих часов:**")
            st.write(month_data["workingHours"])

        st.markdown("---")


html(
    """
<script>
const doc = window.parent.document;

// Create and style notification element
const notification = document.createElement('div');
notification.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: rgba(0, 0, 0, 0.8);
    color: white;
    padding: 10px 20px;
    border-radius: 5px;
    z-index: 9999;
    opacity: 0;
    transition: opacity 0.3s ease;
`;

doc.body.appendChild(notification);

const copyable_numbers = doc.querySelectorAll('.copyable-number');

copyable_numbers.forEach(number => {
    number.addEventListener('click', () => {
        navigator.clipboard.writeText(number.dataset.copy).then(() => {
            notification.textContent = 'Скопировано в буфер обмена';
            notification.style.opacity = '1';
            
            setTimeout(() => {
                notification.style.opacity = '0';
            }, 2000);
        });
    });
});
</script>
""",
    height=0,
    width=0,
)
