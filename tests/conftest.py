import pytest

from aceest import create_app


@pytest.fixture
def app(tmp_path, monkeypatch):
    db_file = tmp_path / "test_aceest.db"
    monkeypatch.setattr("aceest.db.DB_NAME", str(db_file))
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret-key",
        }
    )
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def logged_in_client(client):
    client.post(
        "/login",
        data={"username": "admin", "password": "admin"},
        follow_redirects=True,
    )
    return client
