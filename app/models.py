"""Бизнес-логика приложения учёта расходов: валидация и хранилище SQLite."""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CATEGORIES = (
    "food",
    "transport",
    "housing",
    "entertainment",
    "health",
    "education",
    "other",
)

MAX_DESCRIPTION_LENGTH = 200


class ValidationError(ValueError):
    """Ошибка проверки входных данных расхода."""


@dataclass
class Expense:
    id: int | None
    amount: float
    category: str
    description: str
    spent_on: str

    def to_dict(self) -> dict:
        return asdict(self)


def parse_amount(value) -> float:
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError("Сумма должна быть числом") from exc
    if not amount.is_finite() or amount <= 0:
        raise ValidationError("Сумма должна быть больше нуля")
    if amount > Decimal("10000000"):
        raise ValidationError("Сумма слишком большая")
    return float(amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def validate_expense(data: dict) -> Expense:
    """Проверяет словарь с полями расхода и возвращает объект Expense."""
    if not isinstance(data, dict):
        raise ValidationError("Ожидается JSON-объект")

    amount = parse_amount(data.get("amount"))

    category = str(data.get("category", "")).strip().lower()
    if category not in CATEGORIES:
        raise ValidationError(f"Неизвестная категория: {category or '—'}")

    description = str(data.get("description", "")).strip()
    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError("Описание длиннее 200 символов")

    raw_date = data.get("spent_on") or date.today().isoformat()
    try:
        spent_on = date.fromisoformat(str(raw_date)).isoformat()
    except ValueError as exc:
        raise ValidationError("Дата должна быть в формате ГГГГ-ММ-ДД") from exc

    return Expense(
        id=None,
        amount=amount,
        category=category,
        description=description,
        spent_on=spent_on,
    )


class ExpenseStore:
    """Хранилище расходов поверх SQLite."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    amount REAL NOT NULL CHECK (amount > 0),
                    category TEXT NOT NULL,
                    description TEXT NOT NULL DEFAULT '',
                    spent_on TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _row_to_expense(row: sqlite3.Row) -> Expense:
        return Expense(
            id=row["id"],
            amount=row["amount"],
            category=row["category"],
            description=row["description"],
            spent_on=row["spent_on"],
        )

    def add(self, expense: Expense) -> Expense:
        with self._connect() as conn:
            cursor = conn.execute(
                "INSERT INTO expenses (amount, category, description, spent_on) "
                "VALUES (?, ?, ?, ?)",
                (expense.amount, expense.category, expense.description, expense.spent_on),
            )
            expense.id = cursor.lastrowid
        return expense

    def get(self, expense_id: int) -> Expense | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
        return self._row_to_expense(row) if row else None

    def list(self, category: str | None = None, month: str | None = None) -> list[Expense]:
        query = "SELECT * FROM expenses WHERE 1 = 1"
        params: list = []
        if category:
            query += " AND category = ?"
            params.append(category)
        if month:
            query += " AND substr(spent_on, 1, 7) = ?"
            params.append(month)
        query += " ORDER BY spent_on DESC, id DESC"
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_expense(row) for row in rows]

    def delete(self, expense_id: int) -> bool:
        with self._connect() as conn:
            cursor = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        return cursor.rowcount > 0

    def summary(self, month: str | None = None) -> dict:
        expenses = self.list(month=month)
        by_category: dict[str, float] = {}
        for item in expenses:
            by_category[item.category] = round(by_category.get(item.category, 0) + item.amount, 2)
        total = round(sum(item.amount for item in expenses), 2)
        return {
            "count": len(expenses),
            "total": total,
            "by_category": dict(sorted(by_category.items(), key=lambda kv: -kv[1])),
            "month": month,
        }
