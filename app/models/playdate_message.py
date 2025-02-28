from app import db
from datetime import datetime

class PlaydateMessage(db.Model):
    """Model for messages in a playdate group chat"""
    id = db.Column(db.Integer, primary_key=True)
    playdate_id = db.Column(db.Integer, db.ForeignKey('playdate.id'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define relationships
    playdate = db.relationship('Playdate', backref=db.backref('messages', lazy='dynamic', cascade="all, delete-orphan"))
    sender = db.relationship('User', backref=db.backref('playdate_messages', lazy='dynamic'))
    
    def __repr__(self):
        return f'<PlaydateMessage {self.id}: from {self.sender_id} in playdate {self.playdate_id}>'
    
    def to_dict(self):
        """Convert message to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'playdate_id': self.playdate_id,
            'sender_id': self.sender_id,
            'sender_username': self.sender.username,
            'sender_profile_picture': self.sender.profile_picture,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'formatted_time': self.timestamp.strftime('%I:%M %p')
        } 