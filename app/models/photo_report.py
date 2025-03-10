from app import db
from datetime import datetime

class PhotoReport(db.Model):
    """Model for storing user reports of gallery photos."""
    __tablename__ = 'photo_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    photo_id = db.Column(db.Integer, db.ForeignKey('gallery_photos.id', ondelete='CASCADE'), nullable=False)
    reason = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending', nullable=False)  # 'pending', 'reviewed', 'dismissed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define unique constraint to prevent multiple reports from the same user
    __table_args__ = (db.UniqueConstraint('user_id', 'photo_id', name='_user_photo_report_uc'),)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('photo_reports', lazy=True, cascade='all, delete-orphan'))
    photo = db.relationship('GalleryPhoto', backref=db.backref('reports', lazy=True, cascade='all, delete-orphan'))
    
    def __repr__(self):
        return f'<PhotoReport user_id={self.user_id} photo_id={self.photo_id} status={self.status}>' 