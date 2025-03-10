#!/usr/bin/env python
"""
Deep Admin Check Script

This script performs a comprehensive check of admin users in the database
and tests various methods to evaluate admin status.
"""

from app import create_app, db
from app.models.user import User
from flask import session
from flask_login import current_user
import sys

app = create_app()

def check_admin_db():
    """Check admin status directly in the database"""
    with app.app_context():
        # Get all users
        all_users = User.query.all()
        print(f"Total users in database: {len(all_users)}")
        
        # Check for admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        print(f"\nAdmin users ({len(admin_users)}):")
        for user in admin_users:
            print(f"  - {user.username} (ID: {user.id}, is_admin: {user.is_admin}, type: {type(user.is_admin).__name__})")
        
        # Check for admin in username
        admin_name_users = User.query.filter(User.username.ilike('%admin%')).all()
        print(f"\nUsers with 'admin' in username ({len(admin_name_users)}):")
        for user in admin_name_users:
            print(f"  - {user.username} (ID: {user.id}, is_admin: {user.is_admin}, type: {type(user.is_admin).__name__})")
        
        # Check specific 'admin' user
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            print(f"\nUser 'admin' details:")
            print(f"  - ID: {admin_user.id}")
            print(f"  - Email: {admin_user.email}")
            print(f"  - is_admin: {admin_user.is_admin}")
            print(f"  - is_admin type: {type(admin_user.is_admin).__name__}")
            
            # Test equality with True
            print(f"  - is_admin == True: {admin_user.is_admin == True}")
            print(f"  - is_admin is True: {admin_user.is_admin is True}")
            
            # Test boolean conversion
            print(f"  - bool(is_admin): {bool(admin_user.is_admin)}")
            
            # Test property access
            if hasattr(admin_user, 'is_admin'):
                print(f"  - has is_admin attribute: Yes")
            else:
                print(f"  - has is_admin attribute: No")
                
            # Check if it's a property
            if isinstance(getattr(User, 'is_admin', None), property):
                print(f"  - is_admin is a property")
            else:
                print(f"  - is_admin is a regular attribute")
        else:
            print("\nNo user with username 'admin' found")

def fix_admin_user():
    """Ensure admin user exists and has proper admin privileges"""
    with app.app_context():
        admin_user = User.query.filter_by(username='admin').first()
        
        if admin_user:
            print(f"Found admin user: {admin_user.username}")
            
            # Force admin flag to True
            if not admin_user.is_admin:
                print("Setting is_admin flag to True")
                admin_user.is_admin = True
                db.session.commit()
            else:
                print("Admin flag is already True")
        else:
            print("Admin user not found")
            
def main():
    """Run the admin checks"""
    check_admin_db()
    
    if len(sys.argv) > 1 and sys.argv[1] == '--fix':
        print("\n=== FIXING ADMIN USER ===")
        fix_admin_user()
        print("\n=== RECHECKING AFTER FIX ===")
        check_admin_db()

if __name__ == "__main__":
    main() 