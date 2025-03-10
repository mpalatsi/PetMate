#!/usr/bin/env python
"""
Port Check and Free Utility

A simplified script to check and free port 5006.
Run this script directly to check and automatically free the port.

Usage:
    python scripts/port_check.py
"""

import os
import sys
import socket
import subprocess
import platform

PORT = 5006

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
    
    return None

def kill_process(pid):
    """Kill a process by its PID"""
    try:
        if platform.system() == 'Windows':
            subprocess.run(f'taskkill /F /PID {pid}', shell=True, check=True)
        else:
            import signal
            os.kill(pid, signal.SIGTERM)
            
        print(f"✅ Successfully terminated process with PID {pid}")
        return True
    except Exception as e:
        print(f"❌ Failed to kill process with PID {pid}: {e}")
        return False

def main():
    """Check and automatically free port 5006"""
    print(f"Checking if port {PORT} is in use...")
    
    if not is_port_in_use(PORT):
        print(f"✅ Port {PORT} is free and available for use.")
        return True
    
    print(f"⚠️ Port {PORT} is currently in use.")
    pid = find_process_by_port(PORT)
    
    if not pid:
        print(f"❌ Could not identify the process using port {PORT}.")
        return False
    
    print(f"Process with PID {pid} is using port {PORT}. Terminating automatically.")
    return kill_process(pid)

if __name__ == "__main__":
    sys.exit(0 if main() else 1) 