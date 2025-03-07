from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    # Add the name column if it doesn't exist
    try:
        db.session.execute('ALTER TABLE user ADD COLUMN name VARCHAR(120)')
        db.session.commit()
        print("Added name column to user table")
    except Exception as e:
        print(f"Error adding column (it might already exist): {e}")
        db.session.rollback()
    
    # Update existing users to have their username as their name if name is NULL
    try:
        db.session.execute('UPDATE user SET name = username WHERE name IS NULL')
        db.session.commit()
        print("Updated existing users to have their username as their name")
    except Exception as e:
        print(f"Error updating names: {e}")
        db.session.rollback() 