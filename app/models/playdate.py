from app import db
from datetime import datetime
from app.models.associations import playdate_attendees, playdate_pets

class Playdate(db.Model):
    __tablename__ = 'playdates'
    
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(200), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    duration = db.Column(db.Integer)  # Duration in minutes
    max_attendees = db.Column(db.Integer)
    max_pets = db.Column(db.Integer)  # Maximum number of pets allowed
    status = db.Column(db.String(20), default='scheduled')  # scheduled, in_progress, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    host = db.relationship('User', foreign_keys=[host_id])
    attendees = db.relationship('User', secondary=playdate_attendees)
    pets = db.relationship('Pet', secondary=playdate_pets, backref=db.backref('playdates', lazy=True))
    
    def __repr__(self):
        return f'<Playdate {self.id}: {self.title}>' 