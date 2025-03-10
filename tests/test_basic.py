import unittest
from flask import url_for
from app import create_app, db
from config import TestingConfig

class TestBasic(unittest.TestCase):
    def setUp(self):
        """Set up test environment before each test method is run"""
        self.app = create_app(TestingConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client(use_cookies=True)
    
    def tearDown(self):
        """Clean up after each test method is run"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_index_page(self):
        """Test the index page is accessible"""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_login_page(self):
        """Test the login page is accessible"""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
    
    def test_register_page(self):
        """Test the register page is accessible"""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main() 