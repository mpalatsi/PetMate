import os
import sys
from datetime import datetime, timedelta

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import User
from app.models.pet import Pet
from app.models.playdate import Playdate
from app.models.message import Message
from app.models.review import Review

app = create_app()

def add_test_data():
    print("\nCreating test data...")
    
    # Drop all tables and recreate them
    with app.app_context():
        print("Dropping all tables...")
        db.drop_all()
        print("Creating all tables...")
        db.create_all()
    
    # Create test users
    users = [
        User(
            username='admin',
            email='admin@example.com',
            name='Admin User',
            location='New York, NY',
            bio='Site Administrator',
            preferred_meetup_types='all',
            availability='flexible',
            pet_owner_since=2018,
            pet_experience_level='expert',
            created_at=datetime.utcnow(),
            is_admin=True
        ),
        User(
            username='john_doe',
            email='john@example.com',
            name='John Doe',
            location='New York, NY',
            bio='Dog lover and outdoor enthusiast',
            preferred_meetup_types='parks,beaches',
            availability='weekends,evenings',
            pet_owner_since=2020,
            pet_experience_level='intermediate',
            created_at=datetime.utcnow()
        ),
        User(
            username='jane_smith',
            email='jane@example.com',
            name='Jane Smith',
            location='Brooklyn, NY',
            bio='Cat mom and coffee addict',
            preferred_meetup_types='indoor,parks',
            availability='weekdays,evenings',
            pet_owner_since=2019,
            pet_experience_level='expert',
            created_at=datetime.utcnow()
        ),
        User(
            username='mike_wilson',
            email='mike@example.com',
            name='Mike Wilson',
            location='Queens, NY',
            bio='Pet sitter and dog trainer',
            preferred_meetup_types='parks,training',
            availability='flexible',
            pet_owner_since=2018,
            pet_experience_level='expert',
            created_at=datetime.utcnow()
        )
    ]
    
    for user in users:
        print(f"\nCreating user: {user.username}")
        user.set_password('password123')
        db.session.add(user)
        db.session.flush()
        print(f"Created user: {user.username}")
    
    # Create test pets
    pets = [
        Pet(
            owner_id=users[0].id,
            name='Max',
            species='dog',
            breed='Golden Retriever',
            age=3,
            size='large',
            gender='male',
            bio='Friendly and playful, loves to fetch',
            energy_level='high',
            friendliness='outgoing',
            training_level='intermediate',
            special_needs='None',
            preferred_playmates='all dogs'
        ),
        Pet(
            owner_id=users[1].id,
            name='Luna',
            species='cat',
            breed='Siamese',
            age=2,
            size='medium',
            gender='female',
            bio='Sweet and gentle, loves to cuddle',
            energy_level='medium',
            friendliness='moderate',
            training_level='basic',
            special_needs='None',
            preferred_playmates='calm cats'
        ),
        Pet(
            owner_id=users[2].id,
            name='Bella',
            species='dog',
            breed='German Shepherd',
            age=4,
            size='large',
            gender='female',
            bio='Well-trained and protective',
            energy_level='high',
            friendliness='moderate',
            training_level='advanced',
            special_needs='None',
            preferred_playmates='large dogs'
        )
    ]
    
    for pet in pets:
        print(f"\nCreating pet: {pet.name}")
        db.session.add(pet)
        db.session.flush()
        print(f"Created pet: {pet.name}")
    
    # Create test playdates
    playdates = [
        Playdate(
            host_id=users[0].id,
            title='Central Park Playdate',
            description='Join us for a fun day at Central Park!',
            location='Central Park, New York',
            date=datetime.utcnow() + timedelta(days=7),
            duration=120,
            max_attendees=10,
            status='scheduled'
        ),
        Playdate(
            host_id=users[1].id,
            title='Indoor Cat Social',
            description='Indoor playdate for cats at a local pet cafe',
            location='Paws & Coffee, Brooklyn',
            date=datetime.utcnow() + timedelta(days=14),
            duration=90,
            max_attendees=8,
            status='scheduled'
        )
    ]
    
    for playdate in playdates:
        print(f"\nCreating playdate: {playdate.title}")
        db.session.add(playdate)
        db.session.flush()
        print(f"Created playdate: {playdate.title}")
    
    # Create test messages
    messages = [
        Message(
            sender_id=users[0].id,
            recipient_id=users[1].id,
            content='Hi! Would you like to set up a playdate?',
            is_read=False
        ),
        Message(
            sender_id=users[1].id,
            recipient_id=users[0].id,
            content='Sure! When are you free?',
            is_read=True
        )
    ]
    
    for message in messages:
        print(f"\nCreating message from {message.sender_id} to {message.recipient_id}")
        db.session.add(message)
        db.session.flush()
        print(f"Created message")
    
    # Create test reviews
    reviews = [
        Review(
            reviewer_id=users[0].id,
            reviewed_user_id=users[1].id,
            playdate_id=playdates[0].id,
            rating=5,
            comment='Great playdate! Luna is so friendly.'
        ),
        Review(
            reviewer_id=users[1].id,
            reviewed_user_id=users[0].id,
            playdate_id=playdates[0].id,
            rating=4,
            comment='Max is very well-behaved!'
        )
    ]
    
    for review in reviews:
        print(f"\nCreating review from {review.reviewer_id} to {review.reviewed_user_id}")
        db.session.add(review)
        db.session.flush()
        print(f"Created review")
    
    try:
        db.session.commit()
        print("\nTest data added successfully!")
    except Exception as e:
        db.session.rollback()
        print(f"\nError adding test data: {str(e)}")

if __name__ == '__main__':
    with app.app_context():
        add_test_data() 