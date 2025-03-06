#!/usr/bin/env python
"""
Script to update the PostgreSQL database password.
Run this inside the database container to change the password
for the petmate user to match your configuration.
"""
import os
import sys
import subprocess

def run_postgres_command(sql_command):
    """Run a PostgreSQL command as the postgres superuser."""
    try:
        result = subprocess.run(
            ['psql', '-U', 'postgres', '-c', sql_command],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error executing PostgreSQL command: {e}")
        print(f"stderr: {e.stderr}")
        return None

def update_password(username, new_password):
    """Update the password for a PostgreSQL user."""
    # Escape single quotes in the password
    escaped_password = new_password.replace("'", "''")
    
    # SQL command to update the password
    sql_command = f"ALTER USER {username} WITH PASSWORD '{escaped_password}';"
    
    print(f"Updating password for user '{username}'...")
    result = run_postgres_command(sql_command)
    
    if result is not None:
        print(f"Password updated successfully for user '{username}'.")
        return True
    else:
        print(f"Failed to update password for user '{username}'.")
        return False

def main():
    """Main function to update the database password."""
    # Get the username and password from environment variables or use defaults
    username = os.environ.get('POSTGRES_USER', 'petmate')
    new_password = os.environ.get('POSTGRES_PASSWORD', 'petmatepassword')
    
    print(f"Updating password for PostgreSQL user '{username}'")
    
    # Update the password
    if update_password(username, new_password):
        print("Password update completed successfully.")
    else:
        print("Password update failed.")
        sys.exit(1)
    
    print("\nTo use the updated password:")
    print("1. Update your .env and docker-compose files with the new password")
    print("2. Restart your application to use the new password")

if __name__ == '__main__':
    main() 