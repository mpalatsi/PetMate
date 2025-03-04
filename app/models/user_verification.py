from datetime import datetime
from . import db

class UserVerification(db.Model):
    __tablename__ = 'user_verifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # ID, License, etc.
    document_number = db.Column(db.String(100))
    verification_status = db.Column(db.String(20), default='Pending')  # Pending, Verified, Rejected
    verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    rejection_reason = db.Column(db.Text)

    user = db.relationship('User', backref=db.backref('verification', uselist=False)) 