# ExpenseTracker — CI/CD для приложения учёта расходов

[![CI/CD Pipeline](https://github.com/samai-stack/expense-tracker-cicd/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/samai-stack/expense-tracker-cicd/actions/workflows/ci-cd.yml)

Учебный проект СРО №1 по дисциплине «DevOps инженерия»: веб-приложение учёта личных расходов
(Python + Flask + SQLite) и CI/CD-конвейер на GitHub Actions.

## Возможности

- добавление, просмотр и удаление расходов (веб-форма и REST API);
- категории расходов и фильтр по месяцу;
- сводка: общая сумма и суммы по категориям;
- `GET /health` — проверка состояния сервиса.

| Метод | Путь | Описание |
|---|---|---|
| GET | `/` | веб-интерфейс |
| GET | `/health` | статус, версия, окружение |
| GET | `/api/categories` | список категорий |
| GET | `/api/expenses?category=&month=` | список расходов |
| POST | `/api/expenses` | добавить расход |
| GET / DELETE | `/api/expenses/<id>` | получить / удалить расход |
| GET | `/api/summary?month=` | сводка по расходам |

## Локальный запуск

```bash
pip install -r requirements-dev.txt
python wsgi.py            # http://localhost:8000
pytest --cov=app          # тесты
ruff check . && ruff format --check .   # качество кода
```

Через Docker:

```bash
docker build -t expense-tracker .
docker run -p 8000:8000 expense-tracker
```

## CI/CD-конвейер

Файл: `.github/workflows/ci-cd.yml`. Запуск: push и pull request в `main`, вручную (workflow_dispatch).

1. **Code Quality** — `ruff check` (линтер) и `ruff format --check` (стиль).
2. **Tests** — pytest на Python 3.11 и 3.12, покрытие не ниже 85 %, отчёты JUnit и coverage.xml.
3. **Build Artifact** — сборка Docker-образа, архив образа и исходников, `build-info.json`.
4. **Deploy to Test Environment** — загрузка образа, запуск контейнера, health-check и smoke-тесты API.
