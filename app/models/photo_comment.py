from app import db
from datetime import datetime

class PhotoComment(db.Model):
    """Model for storing user comments on gallery photos."""
    __tablename__ = 'photo_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('gallery_photos.id', ondelete='CASCADE'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('photo_comments', lazy=True, cascade='all, delete-orphan'))
    photo = db.relationship('GalleryPhoto', backref=db.backref('comments', lazy=True, cascade='all, delete-orphan', order_by='PhotoComment.created_at.desc()'))
    
    def __repr__(self):
        return f'<PhotoComment user_id={self.user_id} photo_id={self.photo_id}>' 