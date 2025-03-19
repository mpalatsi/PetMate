#!/usr/bin/env python3
"""
Simple script to run a single Selenium test for validation purposes.
"""
import sys
import os
import time
import subprocess
import traceback
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import socket
import unittest
import importlib

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Define Flask port constant
FLASK_PORT = 5001

def check_server_running(port=FLASK_PORT):
    """Check if a server is running on the specified port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

def start_flask_server():
    """Start the Flask server."""
    # Check if server is already running
    if check_server_running(FLASK_PORT):
        print(f"Server already running on port {FLASK_PORT}.")
        return None
    
    # Start Flask server with app.py
    print(f"Starting Flask server on port {FLASK_PORT}...")
    flask_process = subprocess.Popen([sys.executable, 'app.py'],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
    
    # Wait for server to start
    print("Waiting for server to start...")
    attempts = 0
    
    while attempts < 10:
        if check_server_running(FLASK_PORT):
            print("Flask server started successfully.")
            return flask_process
        
        # Check if process is still running
        if flask_process.poll() is not None:
            stdout, stderr = flask_process.communicate()
            print("Flask server failed to start!")
            print(f"STDOUT: {stdout.decode('utf-8')}")
            print(f"STDERR: {stderr.decode('utf-8')}")
            return None
        
        attempts += 1
        time.sleep(2)
    
    print("Timed out waiting for Flask server to start.")
    if flask_process.poll() is None:
        flask_process.terminate()
    return None

def run_single_test(test_class, test_method=None):
    """Run a single test class or method."""
    print(f"\nRunning test: {test_class}" + (f"::{test_method}" if test_method else ""))
    
    # Import the test module
    try:
        alt_test = importlib.import_module('alt_test')
        
        # Get the test class
        if hasattr(alt_test, test_class):
            test_class_obj = getattr(alt_test, test_class)
            
            # Create test suite
            if test_method:
                # Run specific test method
                suite = unittest.TestSuite()
                suite.addTest(test_class_obj(test_method))
            else:
                # Run all methods in the class
                suite = unittest.TestLoader().loadTestsFromTestCase(test_class_obj)
            
            # Run the tests
            result = unittest.TextTestRunner(verbosity=2).run(suite)
            return result.wasSuccessful()
        else:
            print(f"Error: Test class '{test_class}' not found in alt_test.py")
            print("Available test classes:")
            for name in dir(alt_test):
                obj = getattr(alt_test, name)
                if isinstance(obj, type) and issubclass(obj, unittest.TestCase) and obj != unittest.TestCase:
                    print(f"  - {name}")
            return False
    except Exception as e:
        print(f"Error running test: {e}")
        traceback.print_exc()
        return False

def main():
    """Main entry point."""
    print("=== PetMate Single Test Runner ===\n")
    
    # Check for test class argument
    if len(sys.argv) < 2:
        print("Error: Please specify a test class name")
        print("Usage: python run_single_test.py TestClassName [test_method_name]")
        return 1
    
    test_class = sys.argv[1]
    test_method = sys.argv[2] if len(sys.argv) > 2 else None
    
    flask_process = None
    
    try:
        # Start Flask server if needed
        if check_server_running(FLASK_PORT):
            print(f"Using existing Flask server on port {FLASK_PORT}")
            user_server = True
        else:
            flask_process = start_flask_server()
            if not flask_process:
                print("Cannot continue tests without Flask server.")
                return 1
            user_server = False
        
        # Run the specified test
        exit_code = 0 if run_single_test(test_class, test_method) else 1
        
        print(f"\nTest completed with exit code: {exit_code}")
        return exit_code
        
    except KeyboardInterrupt:
        print("\nTest runner interrupted by user.")
        return 130
    finally:
        # Cleanup Flask server if we started it
        if flask_process and flask_process.poll() is None:
            print("Stopping Flask server...")
            flask_process.terminate()
            try:
                flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                flask_process.kill()
            print("Flask server stopped.")
        elif not user_server:
            print("No Flask process to terminate.")

if __name__ == "__main__":
    sys.exit(main()) 