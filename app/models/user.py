from app import db
from datetime import datetime
from app.models.associations import playdate_attendees
from flask import session
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    name = db.Column(db.String(120))  # User's full name
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile_picture = db.Column(db.String(255))  # Store the filename of uploaded image
    bio = db.Column(db.Text)  # User bio
    location = db.Column(db.String(200))  # User location
    
    # Admin and account status fields
    is_admin = db.Column(db.Boolean, default=False)
    account_status = db.Column(db.String(20), default='active')  # active, suspended, banned
    last_login = db.Column(db.DateTime)
    account_notes = db.Column(db.Text)  # Admin notes about the user
    
    # Pet owner specific fields
    preferred_meetup_types = db.Column(db.String(255))  # e.g., "parks,beaches,dog runs"
    availability = db.Column(db.String(255))  # e.g., "weekends,evenings"
    pet_owner_since = db.Column(db.Integer)  # Year they became a pet owner
    pet_experience_level = db.Column(db.String(50))  # e.g., "beginner", "intermediate", "expert"
    
    # Relationships
    pets = db.relationship('Pet', backref='owner', lazy=True)
    hosted_playdates = db.relationship('Playdate', foreign_keys='Playdate.host_id', lazy=True)
    attended_playdates = db.relationship('Playdate', secondary=playdate_attendees, lazy=True)
    reviews_received = db.relationship('Review', 
                                     foreign_keys='Review.reviewed_user_id',
                                     back_populates='reviewed_user',
                                     lazy='joined')
    reviews_given = db.relationship('Review',
                                  foreign_keys='Review.reviewer_id',
                                  back_populates='reviewer',
                                  lazy='joined')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)
    
    @property
    def is_active(self):
        return self.account_status == 'active'
    
    @property
    def is_authenticated(self):
        return True
    
    @property
    def is_anonymous(self):
        return False
    
    # Admin specific methods
    def suspend_account(self, reason=None):
        self.account_status = 'suspended'
        if reason:
            self.account_notes = f"{datetime.utcnow()}: Suspended - {reason}\n" + (self.account_notes or "")
        db.session.commit()
    
    def activate_account(self, note=None):
        self.account_status = 'active'
        if note:
            self.account_notes = f"{datetime.utcnow()}: Activated - {note}\n" + (self.account_notes or "")
        db.session.commit()
    
    def ban_account(self, reason=None):
        self.account_status = 'banned'
        if reason:
            self.account_notes = f"{datetime.utcnow()}: Banned - {reason}\n" + (self.account_notes or "")
        db.session.commit()
    
    def add_admin_note(self, note):
        self.account_notes = f"{datetime.utcnow()}: {note}\n" + (self.account_notes or "")
        db.session.commit()
    
    def get_unread_message_count(self):
        from app.models.message import Message
        return Message.query.filter_by(recipient_id=self.id, is_read=False).count()

    def get_conversations(self):
        from app.models.message import Message
        # Get all users this user has exchanged messages with
        sent_to = db.session.query(Message.recipient_id).filter_by(sender_id=self.id).distinct()
        received_from = db.session.query(Message.sender_id).filter_by(recipient_id=self.id).distinct()
        
        # Combine and get unique user IDs
        user_ids = [user_id for (user_id,) in sent_to.union(received_from)]
        
        # Get the actual users
        users = User.query.filter(User.id.in_(user_ids)).all()
        
        # For each user, get the most recent message
        conversations = []
        for user in users:
            latest_message = Message.query.filter(
                ((Message.sender_id == self.id) & (Message.recipient_id == user.id)) |
                ((Message.sender_id == user.id) & (Message.recipient_id == self.id))
            ).order_by(Message.timestamp.desc()).first()
            
            unread_count = Message.query.filter_by(
                sender_id=user.id, 
                recipient_id=self.id, 
                is_read=False
            ).count()
            
            conversations.append({
                'user': user,
                'latest_message': latest_message,
                'unread_count': unread_count
            })
        
        # Sort by latest message timestamp
        conversations.sort(key=lambda x: x['latest_message'].timestamp, reverse=True)
        return conversations

    def get_average_rating(self):
        # Use already loaded reviews_received relationship
        reviews = self.reviews_received
        if not reviews:
            return 0
        total = sum(review.rating for review in reviews)
        return round(total / len(reviews), 1)

    def get_reviews_count(self):
        from app.models.review import Review
        return Review.query.filter_by(reviewed_user_id=self.id).count()

    def can_review_user(self, user_id):
        from app.models.playdate import Playdate
        from app.models.review import Review
        # Check if users have had a playdate together
        # and the current user hasn't already reviewed this user for this playdate
        shared_playdates = Playdate.query.join(playdate_attendees, Playdate.id == playdate_attendees.c.playdate_id)\
            .filter(playdate_attendees.c.user_id == self.id)\
            .filter(Playdate.id.in_(
                db.session.query(playdate_attendees.c.playdate_id)
                .filter(playdate_attendees.c.user_id == user_id)
            ))\
            .filter(Playdate.date < datetime.utcnow())\
            .all()
        
        if not shared_playdates:
            return False
        
        # Check if already reviewed for these playdates
        for playdate in shared_playdates:
            existing_review = Review.query.filter_by(
                reviewer_id=self.id,
                reviewed_user_id=user_id,
                playdate_id=playdate.id
            ).first()
            
            if not existing_review:
                return True
        
        return False

    def __repr__(self):
        return f'<User {self.username}>' 