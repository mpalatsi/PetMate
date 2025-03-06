from app import db
from datetime import datetime
from app.models.associations import playdate_pets

class Pet(db.Model):
    __tablename__ = 'pets'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer)
    size = db.Column(db.String(20))  # Small, Medium, Large
    gender = db.Column(db.String(20))
    image_filename = db.Column(db.String(255))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Personality traits and preferences
    energy_level = db.Column(db.String(20))  # Low, Medium, High
    friendliness = db.Column(db.String(20))  # Shy, Moderate, Outgoing
    training_level = db.Column(db.String(20))  # Basic, Intermediate, Advanced
    special_needs = db.Column(db.Text)
    preferred_playmates = db.Column(db.String(255))  # e.g., "small dogs, cats"
    
    def __repr__(self):
        return f'<Pet {self.name}>' 
        
    @property
    def profile_picture(self):
        """Return the URL for the pet's profile picture or None if no image exists."""
        if self.image_filename:
            return f"/static/pet_images/{self.image_filename}"
        return None 