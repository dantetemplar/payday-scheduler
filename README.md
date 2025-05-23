# Payday Scheduler

Веб-приложение для расчета и планирования выплаты заработной платы с поддержкой российского производственного календаря и расчета налогов.

# [ 🚀 Попробуй! ](https://paydays.streamlit.app/)


https://github.com/user-attachments/assets/05e44b57-f966-4312-be42-416fec398988



## Возможности

- Расчет зарплаты с учетом НДФЛ
- Интеграция с производственным календарем из https://calendar.kuzyak.in
- Планирование выплат с учетом аванса
- Курс доллара из https://www.cbr-xml-daily.ru

## Технологии

- [Python 3.12+](https://www.python.org/downloads/)
- [Streamlit](https://streamlit.io/)

## Установка

Установите зависимости с помощью `uv`:
```bash
uv sync
```

## Использование

1. Запустите приложение:
```bash
streamlit run app.py
```

2. Откройте веб-браузер и перейдите по указанному локальному URL (обычно http://localhost:8501)

## Разработка

- Запуск тестов:
```bash
uv run python -m pytest
```
