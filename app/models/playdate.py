from app import db
from datetime import datetime
from app.models.associations import playdate_pets, playdate_attendees

class Playdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    latitude = db.Column(db.Float, nullable=True)  # Store latitude coordinate
    longitude = db.Column(db.Float, nullable=True)  # Store longitude coordinate
    status = db.Column(db.String(20), default='active')  # active, cancelled
    max_pets = db.Column(db.Integer, default=10)  # Maximum number of pets allowed
    
    # Relationships
    host = db.relationship('User', backref='hosted_playdates', foreign_keys=[host_id])
    
    # Fix the attendees relationship by explicitly defining the join conditions
    attendees = db.relationship(
        'User',
        secondary=playdate_attendees,
        backref=db.backref('attending_playdates', lazy='dynamic'),
        primaryjoin=(id == playdate_attendees.c.playdate_id),
        secondaryjoin=('User.id == playdate_attendees.c.user_id')
    )

    # Relationship to playdate photos
    photos = db.relationship('PlaydatePhoto', backref='playdate', lazy=True, cascade="all, delete-orphan")
    
    # Relationship to reviews
    reviews = db.relationship('Review', backref='playdate', lazy=True)
    
    def __repr__(self):
        return f'<Playdate {self.id}: {self.location} on {self.date}>' 