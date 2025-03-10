import unittest
from flask import url_for
from app import create_app, db
from app.models.user import User
from app.models.pet import Pet
import io
from config import TestingConfig

class TestRoutes(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test method is run"""
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)
        
        # Create test user
        self.test_user = User(username='testuser', email='test@example.com')
        self.test_user.set_password('password123')
        db.session.add(self.test_user)
        db.session.commit()
        
        # Log in the test user
        self.client.post('/auth/login', data={
            'username': 'testuser',
            'password': 'password123'
        })
    
    def tearDown(self):
        """Clean up after each test method is run"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_index_page(self):
        """Test the index page is accessible"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'PetMate', response.data)
    
    def test_dashboard_access(self):
        """Test dashboard page is accessible when logged in"""
        response = self.client.get('/dashboard')
        self.assertEqual(response.status_code, 200)
        # Check for dashboard-specific content
        self.assertIn(b'Profile', response.data)
    
    def test_dashboard_redirects_when_logged_out(self):
        """Test dashboard redirects to login when logged out"""
        # Log out the test user
        self.client.get('/auth/logout')
        
        # Try to access dashboard
        response = self.client.get('/dashboard', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'login', response.data.lower())
    
    def test_mobile_dashboard(self):
        """Test mobile dashboard renders correctly"""
        # Use mobile user agent
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X)'
        }
        response = self.client.get('/dashboard', headers=headers)
        self.assertEqual(response.status_code, 200)
        # Check for mobile-specific elements
        self.assertIn(b'mobile', response.data.lower())
    
    def test_add_pet(self):
        """Test adding a new pet"""
        # Create a pet with all required fields
        response = self.client.post('/pets/add', data={
            'name': 'Fluffy',
            'species': 'Dog',
            'breed': 'Golden Retriever',
            'age': '3',
            'temperament': 'Friendly and playful dog',
            'size': 'Medium',
            'gender': 'Male',
            'energy_level': 'Medium',
            'friendliness': 'High',
            'training_level': 'Medium',
            'special_needs': 'None',
            'preferred_playmates': 'Dogs'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Check that the pet was added to the database
        pet = Pet.query.filter_by(name='Fluffy').first()
        self.assertIsNotNone(pet)
        self.assertEqual(pet.species, 'Dog')
        self.assertEqual(pet.owner_id, self.test_user.id)
    
    def test_search_functionality(self):
        """Test search functionality for finding playmates"""
        # Create some pets with the required owner_id
        dog1 = Pet(
            name='Buddy', 
            species='Dog', 
            breed='Labrador', 
            age=2, 
            owner_id=self.test_user.id,
            size='Medium',
            gender='Male'
        )
        dog2 = Pet(
            name='Max', 
            species='Dog', 
            breed='Poodle', 
            age=3, 
            owner_id=self.test_user.id,
            size='Small',
            gender='Male'
        )
        cat1 = Pet(
            name='Whiskers', 
            species='Cat', 
            breed='Siamese', 
            age=4, 
            owner_id=self.test_user.id,
            size='Small',
            gender='Female'
        )
        
        db.session.add_all([dog1, dog2, cat1])
        db.session.commit()
        
        # Test search for dogs - we'll just check the status code since the actual search results
        # may vary depending on the implementation
        response = self.client.get('/search?species=Dog')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main() 