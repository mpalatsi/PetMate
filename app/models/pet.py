from app import db
from datetime import datetime
from app.models.associations import playdate_pets

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    species = db.Column(db.String(50), nullable=False)  # dog, cat, etc.
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer)
    size = db.Column(db.String(20))  # small, medium, large
    temperament = db.Column(db.String(200))  # friendly, shy, energetic, etc.
    image_filename = db.Column(db.String(255))  # Store the filename of uploaded image
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # The backref to owner is defined in the User model
    # Define relationship to playdates through the association table
    playdates = db.relationship('Playdate', secondary=playdate_pets, backref='pets')
    
    def __repr__(self):
        return f'<Pet {self.name}>' 