from app import create_app, db
from app.models.user import User
from app.models.pet import Pet
from app.models.playdate import Playdate
from app.models.message import Message
from app.models.review import Review
from app.models.photo import PlaydatePhoto
from app.models.gallery_photo import GalleryPhoto
from app.models.playdate_message import PlaydateMessage
import os

def backup_database():
    """Create a backup of the current database if it exists"""
    if os.path.exists('petmate.db'):
        import shutil
        from datetime import datetime
        backup_name = f'petmate_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy2('petmate.db', backup_name)
        print(f"Created backup: {backup_name}")

app = create_app()

with app.app_context():
    # Backup existing database
    backup_database()
    
    # Drop all tables
    print("Dropping all tables...")
    db.drop_all()
    
    # Create all tables with new schema
    print("Creating all tables with new schema...")
    db.create_all()
    
    # Create a test user
    test_user = User(
        username='test_user',
        email='test@example.com',
        password='password123',
        name='Test User'
    )
    
    try:
        db.session.add(test_user)
        db.session.commit()
        print("Created test user successfully")
    except Exception as e:
        print(f"Error creating test user: {e}")
        db.session.rollback()

print("Database recreation completed!") 