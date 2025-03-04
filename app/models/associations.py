from app import db

# Association table for playdate attendees
playdate_attendees = db.Table('playdate_attendees',
    db.Column('playdate_id', db.Integer, db.ForeignKey('playdates.id', ondelete='CASCADE'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
)

# Association table for playdate pets
playdate_pets = db.Table('playdate_pets',
    db.Column('playdate_id', db.Integer, db.ForeignKey('playdates.id', ondelete='CASCADE'), primary_key=True),
    db.Column('pet_id', db.Integer, db.ForeignKey('pets.id', ondelete='CASCADE'), primary_key=True)
) 