from app import db
from datetime import datetime

class PlaydateMessage(db.Model):
    __tablename__ = 'playdate_messages'

    id = db.Column(db.Integer, primary_key=True)
    playdate_id = db.Column(db.Integer, db.ForeignKey('playdates.id', ondelete='CASCADE'), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    playdate = db.relationship('Playdate', backref=db.backref('messages', lazy=True, cascade='all, delete-orphan'))
    sender = db.relationship('User', backref=db.backref('playdate_messages_sent', lazy=True))

    def __repr__(self):
        return f'<PlaydateMessage {self.id} from {self.sender_id} in playdate {self.playdate_id}>'
