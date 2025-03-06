#!/usr/bin/env python
"""
Development script for PetMate application.
This script will:
1. Set up the development environment
2. Create necessary directories
3. Initialize the database if it doesn't exist
4. Run the application in development mode

Usage:
    python dev.py
"""

import os
import sys
from app import create_app, db, socketio

def setup_development_environment():
    """Set up the development environment."""
    print("Setting up development environment...")
    
    # Set environment variables for development
    os.environ['FLASK_APP'] = 'wsgi.py'
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Create uploads directory if it doesn't exist
    uploads_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    os.makedirs(os.path.join(uploads_dir, 'profile_pictures'), exist_ok=True)
    os.makedirs(os.path.join(uploads_dir, 'pet_images'), exist_ok=True)
    os.makedirs(os.path.join(uploads_dir, 'playdate_photos'), exist_ok=True)
    os.makedirs(os.path.join(uploads_dir, 'gallery'), exist_ok=True)
    
    print("Development environment set up successfully!")

def initialize_database(app):
    """Initialize the database if it doesn't exist."""
    print("Initializing database...")
    
    with app.app_context():
        # Check if database exists
        try:
            # Try to query the database
            db.session.execute('SELECT 1')
            print("Database already exists.")
        except Exception:
            # Create database tables
            print("Creating database tables...")
            db.create_all()
            print("Database tables created successfully!")

def run_application(app):
    """Run the application in development mode."""
    print("Starting PetMate application in development mode...")
    print("Access the application at http://localhost:5000")
    
    # Run the application with socketio for WebSocket support
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True,
        log_output=True,
        allow_unsafe_werkzeug=True
    )

def main():
    """Main function to run the development server."""
    # Set up development environment
    setup_development_environment()
    
    # Create Flask app
    app = create_app()
    
    # Initialize database
    initialize_database(app)
    
    # Run application
    run_application(app)

if __name__ == '__main__':
    main() 