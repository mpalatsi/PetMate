from datetime import datetime
from . import db

class IncidentReport(db.Model):
    __tablename__ = 'incident_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    playdate_id = db.Column(db.Integer, db.ForeignKey('playdates.id'), nullable=True)
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