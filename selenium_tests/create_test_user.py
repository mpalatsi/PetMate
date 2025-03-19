#!/usr/bin/env python3
"""Script to create a test user for Selenium testing."""

import os
import sys
from flask import Flask
from werkzeug.security import generate_password_hash
from datetime import datetime

# Add the project root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import app and db
from app import create_app, db
from app.models.user import User

def create_app_context():
    """Create a Flask app context for database operations."""
    try:
        app = create_app()
        return app
    except ImportError as e:
        print(f"Failed to import create_app: {e}")
        sys.exit(1)

def check_test_user_exists(username):
    """Check if a test user with the given username exists in the database.
    
    Args:
        username (str): The username to check for
        
    Returns:
        bool: True if the user exists, False otherwise
    """
    app = create_app_context()
    
    with app.app_context():
        try:
            user = User.query.filter_by(username=username).first()
            return user is not None
        except Exception as e:
            print(f"Error checking if test user exists: {e}")
            return False

def create_test_user(username="test_selenium", password="test_password", email="selenium_test@example.com"):
    """Create a test user for Selenium tests if it doesn't already exist.
    
    Args:
        username (str): Username for the test user
        password (str): Password for the test user
        email (str): Email for the test user
        
    Returns:
        bool: True if user was created or already exists, False on error
    """
    app = create_app_context()
    
    print(f"Flask template folder: {app.template_folder}")
    print(f"Current working directory: {os.getcwd()}")
    
    with app.app_context():
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(username=username).first()
            if existing_user:
                print(f"Test user '{username}' already exists.")
                return True
            
            # Create new test user
            hashed_password = generate_password_hash(password)
            new_user = User(
                username=username,
                password=hashed_password,
                email=email,
                name="Selenium Test User",
                location="Test Location",
                is_admin=False,
                created_at=datetime.now(),
                bio="Test user created for Selenium testing"
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            print(f"Test user '{username}' created successfully.")
            return True
            
        except Exception as e:
            print(f"Error creating test user: {e}")
            if 'db' in locals():
                db.session.rollback()
            return False

if __name__ == "__main__":
    success = create_test_user()
    
    if success:
        print("\nTest user details:")
        print(f"Username: test_selenium")
        print(f"Password: test_password")
        print(f"Email: selenium_test@example.com")
        print("Use these credentials in your Selenium tests.")
        sys.exit(0)
    else:
        print("Failed to create test user.")
        sys.exit(1) 