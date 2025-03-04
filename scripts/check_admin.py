import os
import sys
from datetime import datetime

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User

def check_and_recreate_admin():
    app = create_app()
    with app.app_context():
        # Create all database tables
        print("\nCreating database tables...")
        db.create_all()
        print("Database tables created successfully")

        # Check if users table exists and has the correct columns
        print("\nChecking users table schema...")
        inspector = db.inspect(db.engine)
        columns = inspector.get_columns('users')
        print("Users table columns:")
        for column in columns:
            print(f"- {column['name']}: {column['type']}")

        # Check current admin user
        print("\nChecking for existing admin user...")
        admin = User.query.filter_by(username='admin').first()
        print(f"Current admin user: {admin}")
        if admin:
            print(f"Admin user is_admin: {admin.is_admin}")
            print(f"Admin user is_authenticated: {admin.is_authenticated}")
            print(f"Admin user account_status: {admin.account_status}")
            print(f"Admin user created_at: {admin.created_at}")
            print(f"Admin user password_hash: {admin.password_hash}")

        # Delete existing admin user
        if admin:
            print("\nDeleting existing admin user...")
            db.session.delete(admin)
            db.session.commit()
            print("Deleted existing admin user")

        # Create new admin user with explicit admin flag
        print("\nCreating new admin user...")
        new_admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True,
            account_status='active',
            created_at=datetime.utcnow()
        )
        new_admin.set_password('mypassword')
        db.session.add(new_admin)
        db.session.commit()
        print("Created new admin user with admin privileges")

        # Verify the new admin user
        print("\nVerifying new admin user...")
        verify_admin = User.query.filter_by(username='admin').first()
        print(f"Username: {verify_admin.username}")
        print(f"Is admin: {verify_admin.is_admin}")
        print(f"Account status: {verify_admin.account_status}")
        print(f"Created at: {verify_admin.created_at}")
        print(f"Created at type: {type(verify_admin.created_at)}")
        print(f"Password hash: {verify_admin.password_hash}")

        # Check if we can query the user by username
        print("\nTesting user query...")
        test_user = User.query.filter_by(username='admin').first()
        print(f"Query result: {test_user}")
        if test_user:
            print(f"Found user with username: {test_user.username}")
        else:
            print("No user found with username 'admin'")

if __name__ == '__main__':
    check_and_recreate_admin() 