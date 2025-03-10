from app import db
from datetime import datetime

class PhotoLike(db.Model):
    """Model for storing user likes on gallery photos."""
    __tablename__ = 'photo_likes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('gallery_photos.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define unique constraint to prevent multiple likes from the same user
    __table_args__ = (db.UniqueConstraint('user_id', 'photo_id', name='_user_photo_like_uc'),)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('photo_likes', lazy=True, cascade='all, delete-orphan'))
    photo = db.relationship('GalleryPhoto', backref=db.backref('likes', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<PhotoLike user_id={self.user_id} photo_id={self.photo_id}>' 