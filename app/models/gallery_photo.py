from app import db
from datetime import datetime
import uuid

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
    # New fields
    share_uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True)
    moderation_status = db.Column(db.String(20), default='approved', nullable=False)  # approved, pending, rejected
    featured = db.Column(db.Boolean, default=False)
    view_count = db.Column(db.Integer, default=0)
    
    # Relationships
    pet = db.relationship('Pet', backref=db.backref('gallery_photos', lazy=True, cascade='all, delete-orphan'))
    uploader = db.relationship('User', backref=db.backref('uploaded_gallery_photos', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<GalleryPhoto {self.filename}>'
    
    def generate_share_link(self):
        """Generate a unique sharing link for this photo"""
        if not self.share_uuid:
            self.share_uuid = str(uuid.uuid4())
            db.session.commit()
        return f"/gallery/share/{self.share_uuid}"
    
    def increment_view_count(self):
        """Increment the view count for this photo"""
        self.view_count += 1
        db.session.commit() 