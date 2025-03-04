from app import db
from datetime import datetime

class PlaydatePhoto(db.Model):
    __tablename__ = 'playdate_photos'

    id = db.Column(db.Integer, primary_key=True)
    playdate_id = db.Column(db.Integer, db.ForeignKey('playdates.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    photo_path = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    playdate = db.relationship('Playdate', backref=db.backref('photos', lazy=True, cascade='all, delete-orphan'))
    user = db.relationship('User', backref=db.backref('playdate_photos', lazy=True))

    def __repr__(self):
        return f'<PlaydatePhoto {self.id} from playdate {self.playdate_id}>'
