from app import db
from datetime import datetime

class PlaydatePhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    playdate_id = db.Column(db.Integer, db.ForeignKey('playdate.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    caption = db.Column(db.String(255), nullable=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('User', backref='uploaded_photos')
    
    def __repr__(self):
        return f'<PlaydatePhoto {self.id}: {self.filename}>'