import os
import sys
import pytest
from app import create_app, db

# Add the project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def app():
    """Create and configure a Flask app for testing."""
    # Create a test configuration
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',  # Use in-memory SQLite for tests
        'SERVER_NAME': 'localhost.localdomain',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF protection in tests
    })
    
    # Create the database and the database tables
    with app.app_context():
        db.create_all()
    
    yield app

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """A test CLI runner for the app."""
    return app.test_cli_runner() 