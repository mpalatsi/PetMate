#!/usr/bin/env python3
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
import argparse
import socket
from subprocess import Popen
from app import create_app, db, socketio

def is_port_in_use(port):
    """Check if the specified port is in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_dev_server(debug=True, reload=True, port=5001):
    """
    Start the Flask development server with optional debugging.
    
    Args:
        debug (bool): Enable debug mode
        reload (bool): Enable auto-reload on code changes
        port (int): Port to run the server on
    """
    if is_port_in_use(port):
        print(f"ERROR: Port {port} is already in use! Choose a different port.")
        return False
    
    print(f"Starting development server on port {port}")
    
    # Set environment variables
    env = os.environ.copy()
    env['FLASK_APP'] = 'app.py'
    
    if debug:
        env['FLASK_DEBUG'] = '1'
        print("Debug mode: ENABLED")
    else:
        env['FLASK_DEBUG'] = '0'
        print("Debug mode: DISABLED")
    
    # Construct command
    cmd = [sys.executable, 'app.py']
    
    # Start the process
    try:
        process = Popen(cmd, env=env)
        print(f"Server running at http://localhost:{port}")
        print("Press Ctrl+C to stop the server")
        
        # Wait for the process to complete
        process.wait()
        return True
    except KeyboardInterrupt:
        print("\nShutting down server...")
        process.terminate()
        return True
    except Exception as e:
        print(f"Error starting server: {e}")
        return False

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
    """Command-line entry point."""
    parser = argparse.ArgumentParser(description="PetMate Development Server")
    
    parser.add_argument('--no-debug', action='store_true', 
                       help='Disable debug mode')
    parser.add_argument('--no-reload', action='store_true',
                       help='Disable auto-reload on code changes')
    parser.add_argument('--port', type=int, default=5001,
                       help='Port to run the server on (default: 5001)')
    
    args = parser.parse_args()
    
    success = start_dev_server(
        debug=not args.no_debug,
        reload=not args.no_reload,
        port=args.port
    )
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main()) 