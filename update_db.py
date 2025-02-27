import os
import sqlite3
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

def update_database_schema():
    """Add missing columns to the user table."""
    try:
        # Find the database file
        db_path = 'instance/petmate.db'  # Try the Flask 2.0+ default location
        if not os.path.exists(db_path):
            db_path = 'petmate.db'  # Try the current directory
            
        if not os.path.exists(db_path):
            print(f"Database file not found. Searched in: {os.path.abspath('instance/petmate.db')} and {os.path.abspath('petmate.db')}")
            
            # Try to create the database and tables
            print("Attempting to create database and tables...")
            app = Flask(__name__)
            app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///petmate.db'
            db = SQLAlchemy(app)
            
            # Import models to create tables
            from petmate import User, Pet, Playdate
            
            with app.app_context():
                db.create_all()
                print("Database and tables created successfully!")
            
            db_path = 'petmate.db'
        
        print(f"Using database at: {os.path.abspath(db_path)}")
        
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the user table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
        if not cursor.fetchone():
            print("The 'user' table doesn't exist in the database.")
            print("Available tables:")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            for table in tables:
                print(f"- {table[0]}")
            
            # If there's a 'User' table (capital U), we might need to adjust our query
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='User'")
            if cursor.fetchone():
                print("Found 'User' table instead of 'user'. Adjusting queries...")
                table_name = 'User'
            else:
                print("No user table found. Please make sure the database is properly initialized.")
                return
        else:
            table_name = 'user'
        
        # Check if columns exist
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [column[1] for column in cursor.fetchall()]
        print(f"Existing columns in {table_name} table: {columns}")
        
        # Add missing columns
        if 'preferred_meetup_types' not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN preferred_meetup_types VARCHAR(255)")
            print(f"Added preferred_meetup_types column to {table_name} table")
        
        if 'availability' not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN availability VARCHAR(255)")
            print(f"Added availability column to {table_name} table")
        
        if 'pet_owner_since' not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN pet_owner_since INTEGER")
            print(f"Added pet_owner_since column to {table_name} table")
        
        if 'pet_experience_level' not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN pet_experience_level VARCHAR(50)")
            print(f"Added pet_experience_level column to {table_name} table")
        
        # Commit changes and close connection
        conn.commit()
        conn.close()
        print("Database schema updated successfully!")
        
    except Exception as e:
        print(f"Error updating database schema: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    update_database_schema() 