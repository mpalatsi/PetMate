#!/usr/bin/env python
"""
Server Management Utility

This script helps with starting, stopping, and managing the Flask server:
1. Checks if port 5006 is in use and offers to kill the process
2. Monitors server logs for common errors
3. Provides a clean restart function

Usage:
    python scripts/manage_server.py start
    python scripts/manage_server.py stop
    python scripts/manage_server.py restart
    python scripts/manage_server.py check
"""

import os
import sys
import time
import signal
import socket
import subprocess
import platform
import argparse
import psutil
from pathlib import Path

PORT = 5006
PROJECT_ROOT = Path(__file__).parent.parent.absolute()

def is_port_in_use(port=PORT):
    """Check if the specified port is already in use"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def find_process_by_port(port=PORT):
    """Find the process ID using the specified port"""
    if platform.system() == 'Windows':
        try:
            # On Windows, use netstat to find the process
            output = subprocess.check_output(
                f'netstat -ano | findstr :{port}', 
                shell=True
            ).decode('utf-8')
            
            if not output:
                return None
                
            lines = output.strip().split('\n')
            for line in lines:
                if 'LISTENING' in line:
                    parts = line.strip().split()
                    return int(parts[-1])
                    
        except subprocess.CalledProcessError:
            return None
    else:
        # On Unix-like systems, use lsof
        try:
            output = subprocess.check_output(
                f'lsof -i :{port} -t', 
                shell=True
            ).decode('utf-8')
            if output:
                return int(output.strip())
        except subprocess.CalledProcessError:
            return None
    
    return None

def kill_process(pid):
    """Kill a process by its PID"""
    try:
        if platform.system() == 'Windows':
            subprocess.run(f'taskkill /F /PID {pid}', shell=True, check=True)
        else:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)
            # Check if process still exists
            if psutil.pid_exists(pid):
                os.kill(pid, signal.SIGKILL)
                
        print(f"✅ Successfully terminated process with PID {pid}")
        return True
    except (subprocess.CalledProcessError, ProcessLookupError):
        print(f"❌ Failed to kill process with PID {pid}")
        return False

def free_port(port=PORT, force=False):
    """Free up the specified port by killing the process using it"""
    if not is_port_in_use(port):
        print(f"✅ Port {port} is not in use")
        return True
        
    pid = find_process_by_port(port)
    if not pid:
        print(f"⚠️ Port {port} is in use, but could not find the process ID")
        return False
        
    try:
        process = psutil.Process(pid)
        process_name = process.name()
        
        if not force:
            answer = input(f"⚠️ Port {port} is used by process {pid} ({process_name}). Kill it? [y/N] ")
            if answer.lower() != 'y':
                return False
                
        return kill_process(pid)
    except psutil.NoSuchProcess:
        print(f"⚠️ Process {pid} not found")
        return False

def start_server(debug=True):
    """Start the Flask server"""
    if is_port_in_use(PORT):
        print(f"⚠️ Port {PORT} is already in use. Please free it first.")
        return False
        
    try:
        print(f"🚀 Starting server on port {PORT}...")
        env = os.environ.copy()
        
        # Use Python executable from current environment
        python_executable = sys.executable
        
        # Change to project root directory
        os.chdir(PROJECT_ROOT)
        
        # Start the server as a background process
        if platform.system() == 'Windows':
            subprocess.Popen([python_executable, 'run.py'], 
                            env=env, 
                            creationflags=subprocess.CREATE_NEW_CONSOLE)
        else:
            subprocess.Popen([python_executable, 'run.py'], 
                            env=env, 
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            start_new_session=True)
            
        # Wait for server to start
        attempts = 0
        while attempts < 10:
            if is_port_in_use(PORT):
                print(f"✅ Server is now running on port {PORT}")
                return True
            time.sleep(1)
            attempts += 1
            
        print("⚠️ Server did not start within the expected time")
        return False
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

def stop_server(force=True):
    """Stop the Flask server"""
    return free_port(PORT, force)

def restart_server():
    """Restart the Flask server"""
    print("🔄 Restarting server...")
    if stop_server():
        time.sleep(1)  # Allow time for port to be released
        return start_server()
    return False

def check_server_status():
    """Check the status of the Flask server"""
    if is_port_in_use(PORT):
        pid = find_process_by_port(PORT)
        if pid:
            try:
                process = psutil.Process(pid)
                process_name = process.name()
                create_time = time.strftime('%Y-%m-%d %H:%M:%S', 
                                         time.localtime(process.create_time()))
                
                print(f"🟢 Server is running:")
                print(f"   - PID: {pid}")
                print(f"   - Process: {process_name}")
                print(f"   - Started: {create_time}")
                print(f"   - Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")
                return True
            except psutil.NoSuchProcess:
                print(f"⚠️ Port {PORT} is in use, but process {pid} not found")
        else:
            print(f"⚠️ Port {PORT} is in use, but could not find the process ID")
    else:
        print(f"🔴 Server is not running (port {PORT} is free)")
    return False

def main():
    parser = argparse.ArgumentParser(description='Manage the Flask server')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'check'],
                        help='Action to perform')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force stop without confirmation')
    
    args = parser.parse_args()
    
    if args.action == 'start':
        start_server()
    elif args.action == 'stop':
        stop_server(force=args.force)
    elif args.action == 'restart':
        restart_server()
    elif args.action == 'check':
        check_server_status()

if __name__ == '__main__':
    main() 