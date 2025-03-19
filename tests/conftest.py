import os
import sys
import time
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

# Import Selenium components if available
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from webdriver_manager.chrome import ChromeDriverManager
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

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

# Selenium Fixtures
if SELENIUM_AVAILABLE:
    @pytest.fixture(scope="session")
    def selenium_app():
        """Create and configure a Flask app for Selenium testing"""
        app = create_app(TestingConfig)
        app.config.update({
            "TESTING": True,
            "SERVER_NAME": "localhost:5000",
            "PREFERRED_URL_SCHEME": "http"
        })
        
        # Create an application context for the test
        with app.app_context():
            db.create_all()
            
            # Create test user
            test_user = User.query.filter_by(username='selenium_test').first()
            if not test_user:
                test_user = User(username='selenium_test', email='selenium_test@example.com')
                test_user.set_password('test123')
                db.session.add(test_user)
                db.session.commit()
                
            # Create test admin
            admin_user = User.query.filter_by(username='selenium_admin').first()
            if not admin_user:
                admin_user = User(username='selenium_admin', email='selenium_admin@example.com', is_admin=True)
                admin_user.set_password('admin123')
                db.session.add(admin_user)
                db.session.commit()
                
            yield app
            
    @pytest.fixture(scope="session")
    def flask_server(selenium_app):
        """Start a Flask server for Selenium tests"""
        from threading import Thread
        server = Thread(target=selenium_app.run, kwargs={
            'debug': False,
            'use_reloader': False
        })
        server.daemon = True
        server.start()
        
        # Wait for server to start
        time.sleep(1)
        
        yield server

    @pytest.fixture(scope="function")
    def chrome_driver(flask_server):
        """Set up Chrome WebDriver for tests"""
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Uncomment to run headless
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        
        try:
            # Use Selenium's built-in driver management
            driver = webdriver.Chrome(options=chrome_options)
            driver.implicitly_wait(10)  # seconds
            
            yield driver
            
            # Cleanup
            driver.quit()
        except Exception as e:
            print(f"Error setting up Chrome driver: {e}")
            print("Trying alternative approach...")
            
            try:
                # Alternative approach using direct WebDriverManager
                driver_path = ChromeDriverManager().install()
                service = Service(executable_path=driver_path)
                driver = webdriver.Chrome(service=service, options=chrome_options)
                driver.implicitly_wait(10)
                
                yield driver
                
                # Cleanup
                driver.quit()
            except Exception as e:
                print(f"Failed to initialize Chrome driver: {e}")
                pytest.skip("Chrome driver initialization failed")

    @pytest.fixture(scope="session")
    def base_url():
        """Return the base URL for the Flask app"""
        return "http://localhost:5000" 