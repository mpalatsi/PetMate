#!/usr/bin/env python3
"""
Robust script to run Selenium tests for the PetMate application.
"""
import sys
import subprocess
import os
import time
import signal
import traceback
import socket
from urllib.error import URLError
from urllib.request import urlopen

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Constants
FLASK_PORT = 5001
WAIT_TIMEOUT = 30  # seconds

def check_server_running(port=FLASK_PORT):
    """Check if a server is running on the specified port."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    except:
        return False

def start_flask_server():
    """Start the Flask server and wait for it to be ready."""
    print("Starting Flask server...")
    
    # Check if server is already running
    if check_server_running(FLASK_PORT):
        print(f"A server is already running on port {FLASK_PORT}.")
        return None
    
    # Start Flask server with app.py
    flask_process = subprocess.Popen([sys.executable, 'app.py'],
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
    
    print(f"Waiting for Flask server to start on port {FLASK_PORT}...")
    start_time = time.time()
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
    
    print(f"Timed out waiting for Flask server to start after {time.time() - start_time:.2f} seconds")
    if flask_process.poll() is None:
        flask_process.terminate()
    return None

def run_tests():
    """Run Selenium tests and capture results."""
    print("\nRunning Selenium tests...")
    test_command = [sys.executable, 'alt_test.py']
    test_process = subprocess.run(test_command, capture_output=True, text=True)
    
    print("\nTest Results:")
    print(test_process.stdout)
    
    if test_process.stderr:
        print("\nErrors:")
        print(test_process.stderr)
    
    return test_process.returncode

def cleanup(flask_process):
    """Clean up resources."""
    if flask_process:
        print("Shutting down Flask server...")
        try:
            if os.name == 'nt':  # Windows
                flask_process.terminate()
            else:  # Unix-like
                os.killpg(os.getpgid(flask_process.pid), signal.SIGTERM)
            
            # Wait for process to terminate
            flask_process.wait(timeout=5)
            print("Flask server terminated.")
        except Exception as e:
            print(f"Error shutting down server: {e}")
            # Force kill if termination fails
            try:
                flask_process.kill()
                print("Flask server killed.")
            except:
                print("Failed to kill server process.")

def main():
    """Main entry point."""
    print("=== PetMate Selenium Test Runner ===\n")
    
    flask_process = None
    try:
        # Check if server is already running first
        if check_server_running(FLASK_PORT):
            print(f"Flask server already running on port {FLASK_PORT}")
            user_server = True
        else:
            # Start Flask server
            flask_process = start_flask_server()
            if not flask_process:
                print("Cannot continue tests without Flask server.")
                return 1
            user_server = False
        
        # Run Selenium tests
        exit_code = run_tests()
        
        print(f"\nTests completed with exit code: {exit_code}")
        return exit_code
        
    except KeyboardInterrupt:
        print("\nTest runner interrupted by user.")
        return 130
    finally:
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