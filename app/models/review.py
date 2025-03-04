from app import db
from datetime import datetime

class Review(db.Model):
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    reviewed_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    playdate_id = db.Column(db.Integer, db.ForeignKey('playdates.id', ondelete='CASCADE'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviewer = db.relationship('User', 
                             foreign_keys=[reviewer_id],
                             back_populates='reviews_given')
    reviewed_user = db.relationship('User',
                                  foreign_keys=[reviewed_user_id],
                                  back_populates='reviews_received')
    playdate = db.relationship('Playdate', backref=db.backref('reviews', lazy=True))
    
    def __repr__(self):
        return f'<Review {self.id}: {self.rating} stars>' 