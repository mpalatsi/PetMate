from app import create_app, db
import sys
from sqlalchemy import text

# Create the app using the application factory
app = create_app()

with app.app_context():
    try:
        # Add new columns to the playdate table
        db.session.execute(text('''
            ALTER TABLE playdate 
            ADD COLUMN latitude REAL;
        '''))
        db.session.execute(text('''
            ALTER TABLE playdate 
            ADD COLUMN longitude REAL;
        '''))
        
        db.session.commit()
        print("Migration completed successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error during migration: {str(e)}")
        sys.exit(1)