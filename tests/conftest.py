import pytest
from app import create_app
from extensions import db
from models.user import User

@pytest.fixture
def app():
    app = create_app()
    app.config.update({
        "TESTING": True,
    })

    # Teardown logic
    with app.app_context():
        yield app
        
        # Cleanup test users
        users_to_delete = User.query.filter(User.username.like("testuser%")).all()
        for u in users_to_delete:
            db.session.delete(u)
        db.session.commit()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
