from app import create_app, db
import sys
from sqlalchemy import text

# Create the app using the application factory
app = create_app()

with app.app_context():
    try:
        # Add the max_pets column to the playdates table
        db.session.execute(text('''
            ALTER TABLE playdates
            ADD COLUMN max_pets INTEGER;
        '''))
        
        db.session.commit()
        print("Added max_pets column to playdates table successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"Error during database update: {str(e)}")
        sys.exit(1) 