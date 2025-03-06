#!/usr/bin/env python
"""
Script to check the database connection configuration.
This will parse the DATABASE_URL and validate its format.
"""
import os
import sys
import re
from urllib.parse import urlparse

def check_database_url():
    """Check if the DATABASE_URL environment variable is properly formatted."""
    database_url = os.environ.get('DATABASE_URL')
    
    if not database_url:
        print("ERROR: DATABASE_URL environment variable is not set.")
        return False
    
    print(f"Checking DATABASE_URL: {database_url}")
    
    # Parse the URL
    try:
        parsed_url = urlparse(database_url)
        
        # Check scheme
        if parsed_url.scheme != 'postgresql':
            print(f"ERROR: Invalid scheme in DATABASE_URL: {parsed_url.scheme}. Expected 'postgresql'.")
            return False
        
        # Check hostname
        if not parsed_url.hostname:
            print("ERROR: No hostname in DATABASE_URL.")
            return False
        
        # Print components for debugging
        print(f"- Scheme: {parsed_url.scheme}")
        print(f"- Username: {parsed_url.username}")
        print(f"- Password: {'*' * len(parsed_url.password) if parsed_url.password else 'None'}")
        print(f"- Hostname: {parsed_url.hostname}")
        print(f"- Port: {parsed_url.port or 'Default'}")
        print(f"- Database: {parsed_url.path[1:] if parsed_url.path else 'None'}")
        
        # Check for common issues
        if '@' in parsed_url.password:
            print("WARNING: Password contains '@' character which can cause parsing issues.")
            print("Solution: URL-encode the '@' character as '%40' in your password.")
            return False
        
        if ':' in parsed_url.password:
            print("WARNING: Password contains ':' character which can cause parsing issues.")
            print("Solution: URL-encode the ':' character as '%3A' in your password.")
            return False
        
        print("DATABASE_URL format looks valid.")
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to parse DATABASE_URL: {e}")
        return False

def main():
    """Main function to run the script."""
    print("Checking database connection configuration...")
    
    # Check if we can access the environment variables
    if not check_database_url():
        print("\nRecommended actions:")
        print("1. Ensure DATABASE_URL is properly set in your environment or .env file")
        print("2. If your password contains special characters, URL-encode them")
        print("3. For example, change: postgresql://user:p@ssword@host/db")
        print("   To: postgresql://user:p%40ssword@host/db")
        
        print("\nTo manually encode your password, you can use this Python code:")
        print("from urllib.parse import quote_plus")
        print("encoded_password = quote_plus('your-password-with-special-chars')")
        print("print(encoded_password)")
        
        sys.exit(1)
    
    print("\nCongratulations! Your database connection configuration looks valid.")

if __name__ == '__main__':
    main() 