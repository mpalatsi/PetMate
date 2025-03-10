import os
import sys
import pytest
from app import create_app, db
from app.models.user import User
from app.models.pet import Pet
from app.models.gallery_photo import GalleryPhoto
from app.models.message import Message
from datetime import datetime
from config import TestingConfig

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture(scope='module')
def test_app():
    """Create and configure a Flask app for testing"""
    app = create_app(TestingConfig)
    
    # Create a test client
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def test_client(test_app):
    """A test client for the app"""
    with test_app.test_client() as client:
        yield client

@pytest.fixture(scope='function')
def init_database(test_app):
    """Initialize the database with test data"""
    with test_app.app_context():
        # Create users
        admin_user = User(username='admin', email='admin@example.com', is_admin=True)
        admin_user.set_password('password123')
        
        regular_user = User(username='user', email='user@example.com')
        regular_user.set_password('password123')
        
        # Add users to database
        db.session.add(admin_user)
        db.session.add(regular_user)
        db.session.commit()
        
        # Create pets
        pet1 = Pet(
            name='Fluffy', 
            species='Dog', 
            breed='Golden Retriever', 
            age=3, 
            bio='A friendly dog',
            owner_id=regular_user.id
        )
        
        pet2 = Pet(
            name='Whiskers', 
            species='Cat', 
            breed='Siamese', 
            age=2, 
            bio='A playful cat',
            owner_id=regular_user.id
        )
        
        # Add pets to database
        db.session.add(pet1)
        db.session.add(pet2)
        db.session.commit()
        
        # Create photos
        photo1 = GalleryPhoto(
            title='Dog at park',
            description='Fluffy playing at the park',
            filename='dog_park.jpg',
            user_id=regular_user.id,
            pet_id=pet1.id,
            is_public=True,
            created_at=datetime.utcnow()
        )
        
        photo2 = GalleryPhoto(
            title='Cat sleeping',
            description='Whiskers taking a nap',
            filename='cat_sleep.jpg',
            user_id=regular_user.id,
            pet_id=pet2.id,
            is_public=False,
            created_at=datetime.utcnow()
        )
        
        # Add photos to database
        db.session.add(photo1)
        db.session.add(photo2)
        db.session.commit()
        
        yield
        
        # Clean up
        db.session.query(GalleryPhoto).delete()
        db.session.query(Pet).delete()
        db.session.query(User).delete()
        db.session.commit()

@pytest.fixture(scope='function')
def authenticated_admin_client(test_client):
    """A test client that's authenticated as an admin user"""
    # Log in as admin
    test_client.post('/auth/login', data={
        'username': 'admin',
        'password': 'password123'
    })
    yield test_client
    # Log out after test
    test_client.get('/auth/logout')

@pytest.fixture(scope='function')
def authenticated_user_client(test_client):
    """A test client that's authenticated as a regular user"""
    # Log in as regular user
    test_client.post('/auth/login', data={
        'username': 'user',
        'password': 'password123'
    })
    yield test_client
    # Log out after test
    test_client.get('/auth/logout')

@pytest.fixture(scope='function')
def mobile_headers():
    """Headers to simulate a mobile device request"""
    return {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
    } 