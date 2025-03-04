from app import create_app, db
from app.models.user import User
from werkzeug.security import generate_password_hash

def create_test_user():
    app = create_app()
    
    with app.app_context():
        # Check if test user already exists
        existing_user = User.query.filter_by(username='test_user').first()
        if existing_user:
            print("Test user already exists, deleting...")
            db.session.delete(existing_user)
            db.session.commit()
        
        # Create new test user with properly hashed password
        test_user = User(
            username='test_user',
            email='test@example.com',
            name='Test User',
            password_hash=generate_password_hash('password123')
        )
        
        try:
            db.session.add(test_user)
            db.session.commit()
            print("Test user created successfully!")
            print("Username: test_user")
            print("Password: password123")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating test user: {e}")

if __name__ == '__main__':
    create_test_user() 