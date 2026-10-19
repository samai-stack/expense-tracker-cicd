"""Приложение учёта расходов ExpenseTracker (Flask)."""

import os

from flask import Flask

from .models import ExpenseStore

__version__ = "1.0.0"


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        DATABASE=os.environ.get("DATABASE", "expenses.db"),
        APP_ENV=os.environ.get("APP_ENV", "development"),
        APP_VERSION=os.environ.get("APP_VERSION", __version__),
    )
    if config:
        app.config.update(config)

    app.extensions["store"] = ExpenseStore(app.config["DATABASE"])

    from .routes import bp

    app.register_blueprint(bp)
    return app
