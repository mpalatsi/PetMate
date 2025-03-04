from app import db
from datetime import datetime

class GalleryPhoto(db.Model):
    __tablename__ = 'gallery_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    pet_id = db.Column(db.Integer, db.ForeignKey('pets.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    pet = db.relationship('Pet', backref=db.backref('gallery_photos', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<GalleryPhoto {self.filename}>' 