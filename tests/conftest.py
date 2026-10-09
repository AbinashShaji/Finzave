"""
Module: tests/conftest.py

Purpose:
Contains Pytest test cases ensuring application stability.

Flow:
User Request -> Route Handler -> Business Logic -> Database

"""
import pytest
from app import create_app
from extensions import db
from models.user import User

@pytest.fixture
def app():
    # Load config without dotenv to avoid prod DB, or explicitly override
    app = create_app()
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "JWT_COOKIE_CSRF_PROTECT": False,
        "SERVER_NAME": "localhost"
    })

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    with app.app_context():
        user = User(username="test_user", email="test@example.com", password_hash="hash")
        db.session.add(user)
        db.session.commit()
        # Keep a reference or ID. It's safer to just return the ID to avoid detached instance errors.
        yield user.id

@pytest.fixture
def user_session(app, client, test_user):
    from flask_jwt_extended import create_access_token
    with app.app_context():
        token = create_access_token(identity=str(test_user))
    client.set_cookie('access_token_cookie', token)
    return client
