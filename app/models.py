from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class EmergencyContact(db.Model):
    __tablename__ = 'emergency_contacts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    relationship = db.Column(db.String(50), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('emergency_contacts', lazy=True))

class IncidentReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    playdate_id = db.Column(db.Integer, db.ForeignKey('playdate.id'), nullable=True)
    incident_type = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # Minor, Moderate, Severe
    status = db.Column(db.String(20), default='Pending')  # Pending, Under Review, Resolved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolution = db.Column(db.Text)
    resolved_at = db.Column(db.DateTime)

    reporter = db.relationship('User', backref=db.backref('reported_incidents', lazy=True))
    playdate = db.relationship('Playdate', backref=db.backref('incidents', lazy=True))

class UserVerification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)  # ID, License, etc.
    document_number = db.Column(db.String(100))
    verification_status = db.Column(db.String(20), default='Pending')  # Pending, Verified, Rejected
    verified_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    rejection_reason = db.Column(db.Text)

    user = db.relationship('User', backref=db.backref('verification', uselist=False))

# Add relationships to User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Safety and trust fields
    is_verified = db.Column(db.Boolean, default=False)
    accepted_code_of_conduct = db.Column(db.Boolean, default=False)
    code_of_conduct_accepted_at = db.Column(db.DateTime)
    account_status = db.Column(db.String(20), default='Active')  # Active, Suspended, Banned
    suspension_reason = db.Column(db.Text)
    suspension_end_date = db.Column(db.DateTime)

    def has_valid_emergency_contact(self):
        return any(contact.is_primary for contact in self.emergency_contacts)

    def is_account_in_good_standing(self):
        return self.account_status == 'Active' and self.accepted_code_of_conduct 