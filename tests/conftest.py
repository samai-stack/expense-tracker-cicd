import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app({"DATABASE": str(tmp_path / "test.db"), "TESTING": True, "APP_ENV": "test"})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def store(app):
    return app.extensions["store"]
