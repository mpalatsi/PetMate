from app import db
from datetime import datetime

class GalleryPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=True)  # Optional link to a specific pet
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    likes = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('User', backref='gallery_photos')
    pet = db.relationship('Pet', backref='gallery_photos')
    
    def __repr__(self):
        return f'<GalleryPhoto {self.id}: {self.title or "Untitled"}>' 