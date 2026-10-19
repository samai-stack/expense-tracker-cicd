"""HTTP-маршруты: веб-страница и REST API."""

from flask import Blueprint, current_app, jsonify, redirect, render_template, request, url_for

from .models import CATEGORIES, ExpenseStore, ValidationError, validate_expense

bp = Blueprint("expenses", __name__)


def get_store() -> ExpenseStore:
    return current_app.extensions["store"]


@bp.get("/")
def index():
    store = get_store()
    month = request.args.get("month") or None
    return render_template(
        "index.html",
        expenses=store.list(month=month),
        summary=store.summary(month=month),
        categories=CATEGORIES,
        error=request.args.get("error"),
        month=month or "",
    )


@bp.post("/expenses/add")
def add_from_form():
    try:
        expense = validate_expense(request.form.to_dict())
    except ValidationError as exc:
        return redirect(url_for("expenses.index", error=str(exc)))
    get_store().add(expense)
    return redirect(url_for("expenses.index"))


@bp.post("/expenses/<int:expense_id>/delete")
def delete_from_form(expense_id: int):
    get_store().delete(expense_id)
    return redirect(url_for("expenses.index"))


@bp.get("/health")
def health():
    return jsonify(
        status="ok",
        version=current_app.config["APP_VERSION"],
        environment=current_app.config["APP_ENV"],
    )


@bp.get("/api/categories")
def categories():
    return jsonify(list(CATEGORIES))


@bp.get("/api/expenses")
def list_expenses():
    category = request.args.get("category")
    if category and category not in CATEGORIES:
        return jsonify(error=f"Неизвестная категория: {category}"), 400
    month = request.args.get("month")
    return jsonify([e.to_dict() for e in get_store().list(category=category, month=month)])


@bp.post("/api/expenses")
def create_expense():
    try:
        expense = validate_expense(request.get_json(silent=True))
    except ValidationError as exc:
        return jsonify(error=str(exc)), 400
    created = get_store().add(expense)
    return jsonify(created.to_dict()), 201


@bp.get("/api/expenses/<int:expense_id>")
def get_expense(expense_id: int):
    expense = get_store().get(expense_id)
    if expense is None:
        return jsonify(error="Расход не найден"), 404
    return jsonify(expense.to_dict())


@bp.delete("/api/expenses/<int:expense_id>")
def delete_expense(expense_id: int):
    if not get_store().delete(expense_id):
        return jsonify(error="Расход не найден"), 404
    return "", 204


@bp.get("/api/summary")
def summary():
    return jsonify(get_store().summary(month=request.args.get("month")))
