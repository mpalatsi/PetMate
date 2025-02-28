from app import db

# Association table for playdates and pets
playdate_pets = db.Table('playdate_pets',
    db.Column('playdate_id', db.Integer, db.ForeignKey('playdate.id'), primary_key=True),
    db.Column('pet_id', db.Integer, db.ForeignKey('pet.id'), primary_key=True)
)

# Association table for playdate attendees
playdate_attendees = db.Table('playdate_attendees',
    db.Column('playdate_id', db.Integer, db.ForeignKey('playdate.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('status', db.String(20), default='confirmed')  # confirmed, maybe, declined
) 