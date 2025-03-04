from app import create_app, db
from app.models.user import User
from app.models.pet import Pet
from app.models.playdate import Playdate
from app.models.message import Message
from app.models.review import Review
from app.models.photo import PlaydatePhoto
from app.models.gallery_photo import GalleryPhoto
from app.models.playdate_message import PlaydateMessage
import sqlite3
import os
from datetime import datetime

def restore_from_backup():
    # Connect to the backup database
    backup_conn = sqlite3.connect('petmate_backup_20250303_005552.db')
    backup_cur = backup_conn.cursor()
    
    # Create Flask app and get current database connection
    app = create_app()
    
    with app.app_context():
        try:
            # Restore Users
            backup_cur.execute('SELECT * FROM user')
            users = backup_cur.fetchall()
            
            # Get column names from the backup database
            backup_cur.execute('PRAGMA table_info(user)')
            columns = [column[1] for column in backup_cur.fetchall()]
            
            print(f"Found {len(users)} users to restore...")
            
            for user_data in users:
                # Create a dictionary of user data
                user_dict = {columns[i]: value for i, value in enumerate(user_data)}
                
                # Remove id from the dictionary as it will be auto-generated
                user_id = user_dict.pop('id')
                
                # Check if user already exists
                existing_user = User.query.filter_by(username=user_dict['username']).first()
                if not existing_user:
                    try:
                        new_user = User(**user_dict)
                        db.session.add(new_user)
                        print(f"Restored user: {user_dict['username']}")
                    except Exception as e:
                        print(f"Error restoring user {user_dict['username']}: {str(e)}")
                        continue
            
            # Commit the changes
            db.session.commit()
            print("User restoration completed successfully!")
            
            # TODO: Add restoration for other tables (pets, playdates, etc.)
            # We can add these in subsequent steps if needed
            
        except Exception as e:
            print(f"Error during restoration: {str(e)}")
            db.session.rollback()
        finally:
            backup_conn.close()

if __name__ == '__main__':
    restore_from_backup() 