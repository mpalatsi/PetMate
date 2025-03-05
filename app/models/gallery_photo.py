from app import db
from datetime import datetime

class GalleryPhoto(db.Model):
    __tablename__ = 'gallery_photos'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey('pets.id', ondelete='CASCADE'), nullable=True)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_public = db.Column(db.Boolean, default=True)
    caption = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pet = db.relationship('Pet', backref=db.backref('gallery_photos', lazy=True, cascade='all, delete-orphan'))
    uploader = db.relationship('User', backref=db.backref('uploaded_gallery_photos', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<GalleryPhoto {self.filename}>' 