from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

# Create a minimal Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///petmate.db'
db = SQLAlchemy(app)

# Define models with all required columns
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile_picture = db.Column(db.String(255))
    bio = db.Column(db.Text)
    location = db.Column(db.String(200))
    
    # New fields
    preferred_meetup_types = db.Column(db.String(255))
    availability = db.Column(db.String(255))
    pet_owner_since = db.Column(db.Integer)
    pet_experience_level = db.Column(db.String(50))

# Association table for playdates and pets
playdate_pets = db.Table('playdate_pets',
    db.Column('playdate_id', db.Integer, db.ForeignKey('playdate.id'), primary_key=True),
    db.Column('pet_id', db.Integer, db.ForeignKey('pet.id'), primary_key=True)
)

# Association table for playdate attendees
playdate_attendees = db.Table('playdate_attendees',
    db.Column('playdate_id', db.Integer, db.ForeignKey('playdate.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('status', db.String(20), default='confirmed')
)

class Playdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    species = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer)
    size = db.Column(db.String(20))
    temperament = db.Column(db.String(200))
    image_filename = db.Column(db.String(255))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def create_database():
    """Create the database and all tables with the correct schema."""
    try:
        # Create directory for profile pictures if it doesn't exist
        os.makedirs('static/profile_pictures', exist_ok=True)
        
        # Create directory for pet images if it doesn't exist
        os.makedirs('static/pet_images', exist_ok=True)
        
        # Create all tables
        with app.app_context():
            db.create_all()
            print("Database and tables created successfully!")
            
            # Check if tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"Created tables: {tables}")
            
            # Check columns in the user table
            columns = [column['name'] for column in inspector.get_columns('user')]
            print(f"Columns in user table: {columns}")
            
    except Exception as e:
        print(f"Error creating database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_database() 