from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import base64
import time
import random
from alembic import op

# Load environment variables from .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, using environment variables directly

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///petmate.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Required for session management

# Get Google Maps API key from environment variable with a fallback to a placeholder
# This ensures we don't expose API keys in the code
app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY', '')

app.config['UPLOAD_FOLDER'] = 'static/pet_images'
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Initialize Flask-Migrate

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

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    profile_picture = db.Column(db.String(255))  # Existing field for profile picture
    bio = db.Column(db.Text)  # Existing field for user bio
    location = db.Column(db.String(200))  # Existing field for location
    
    # New fields relevant to pet owners
    preferred_meetup_types = db.Column(db.String(255))  # e.g., "parks,beaches,dog runs"
    availability = db.Column(db.String(255))  # e.g., "weekends,evenings"
    pet_owner_since = db.Column(db.Integer)  # Year they became a pet owner
    pet_experience_level = db.Column(db.String(50))  # e.g., "beginner", "intermediate", "expert"
    
    # Define the relationship to the Pet model
    pets = db.relationship('Pet', backref='owner', lazy=True)

    def get_unread_message_count(self):
        return Message.query.filter_by(recipient_id=self.id, is_read=False).count()

    def get_conversations(self):
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
        reviews = Review.query.filter_by(reviewed_user_id=self.id).all()
        if not reviews:
            return 0
        total = sum(review.rating for review in reviews)
        return round(total / len(reviews), 1)

    def get_reviews_count(self):
        return Review.query.filter_by(reviewed_user_id=self.id).count()

    def can_review_user(self, user_id):
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

class Playdate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    host = db.relationship('User', backref='hosted_playdates', foreign_keys=[host_id])
    pets = db.relationship('Pet', secondary=playdate_pets, backref='playdates')
    
    # Fix the attendees relationship by explicitly defining the join conditions
    attendees = db.relationship(
        'User',
        secondary=playdate_attendees,
        backref=db.backref('attending_playdates', lazy='dynamic'),
        primaryjoin=(id == playdate_attendees.c.playdate_id),
        secondaryjoin=(User.id == playdate_attendees.c.user_id)
    )

    # Add this to the Playdate class
    photos = db.relationship('PlaydatePhoto', backref='playdate', lazy=True, cascade="all, delete-orphan")

class Pet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    species = db.Column(db.String(50), nullable=False)  # dog, cat, etc.
    breed = db.Column(db.String(100))
    age = db.Column(db.Integer)
    size = db.Column(db.String(20))  # small, medium, large
    temperament = db.Column(db.String(200))  # friendly, shy, energetic, etc.
    image_filename = db.Column(db.String(255))  # Store the filename of uploaded image
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    # Define relationships
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reviewed_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    playdate_id = db.Column(db.Integer, db.ForeignKey('playdate.id'), nullable=True)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], backref='reviews_given')
    reviewed_user = db.relationship('User', foreign_keys=[reviewed_user_id], backref='reviews_received')
    playdate = db.relationship('Playdate', backref='reviews')
    
    def __repr__(self):
        return f'<Review {self.id}: {self.rating} stars>'

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

class GalleryPhoto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    pet_id = db.Column(db.Integer, db.ForeignKey('pet.id'), nullable=True)  # Optional link to a specific pet
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    likes = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=True)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('User', backref='gallery_photos')
    pet = db.relationship('Pet', backref='gallery_photos')
    
    def __repr__(self):
        return f'<GalleryPhoto {self.id}: {self.title or "Untitled"}>'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']  # In real app, hash this password!
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return render_template('confirmation.html', error='Username already exists')
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return render_template('confirmation.html', error='Email already exists')
        
        new_user = User(username=username, email=email, password=password)
        try:
            db.session.add(new_user)
            db.session.commit()
            return render_template('confirmation.html', username=username, success=True)
        except Exception as e:
            db.session.rollback()
            return render_template('confirmation.html', error=f'Registration error: {str(e)}')
    
    # If GET request, show registration form
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        return render_template('login.html', error='Invalid credentials')
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    email = user.email
    
    # Handle case where user doesn't have the new fields yet
    try:
        # Try to access the new fields
        _ = user.preferred_meetup_types
        _ = user.availability
        _ = user.pet_owner_since
        _ = user.pet_experience_level
    except Exception as e:
        # If there's an error, run the migration
        print(f"Error accessing new fields: {e}")
        print("Attempting to update database schema...")
        try:
            # Add the missing columns directly
            with app.app_context():
                op = db.session.execute("""
                    ALTER TABLE user 
                    ADD COLUMN preferred_meetup_types VARCHAR(255);
                """)
                op = db.session.execute("""
                    ALTER TABLE user 
                    ADD COLUMN availability VARCHAR(255);
                """)
                op = db.session.execute("""
                    ALTER TABLE user 
                    ADD COLUMN pet_owner_since INTEGER;
                """)
                op = db.session.execute("""
                    ALTER TABLE user 
                    ADD COLUMN pet_experience_level VARCHAR(50);
                """)
                db.session.commit()
                print("Database schema updated successfully.")
        except Exception as migration_error:
            print(f"Error updating schema: {migration_error}")
            # Continue anyway, the template will handle missing attributes
    
    return render_template('dashboard.html', username=username, email=email, user=user)

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/static/images/<path:filename>')
def serve_placeholder_image(filename):
    if filename == 'dog1.jpg':
        return redirect('https://placedog.net/300/200?id=1')
    elif filename == 'dog2.jpg':
        return redirect('https://placedog.net/300/200?id=2')
    elif filename == 'dog3.jpg':
        return redirect('https://placedog.net/300/200?id=3')
    elif filename == 'local.jpg':
        return redirect('https://placedog.net/400/300?id=4')
    else:
        return 'Image not found', 404

@app.route('/schedule', methods=['GET', 'POST'])
def schedule():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    
    # Get Google Maps API key from environment or config
    google_maps_api_key = os.environ.get('GOOGLE_MAPS_API_KEY', app.config.get('GOOGLE_MAPS_API_KEY', ''))
    
    if request.method == 'POST':
        # Existing code for handling form submission
        date_str = request.form.get('date')
        location = request.form.get('location')
        description = request.form.get('description')
        selected_pet_ids = request.form.getlist('selected_pets')
        
        # Convert date string to datetime object
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        
        # Create new playdate
        playdate = Playdate(
            host_id=user.id,
            date=date,
            location=location,
            description=description
        )
        
        # Add selected pets to the playdate
        if selected_pet_ids:
            selected_pets = Pet.query.filter(Pet.id.in_(selected_pet_ids)).all()
            playdate.pets = selected_pets
        
        # Add the host as an attendee
        db.session.add(playdate)
        db.session.flush()  # Get the playdate ID
        
        # Add the host as a confirmed attendee
        stmt = playdate_attendees.insert().values(
            playdate_id=playdate.id,
            user_id=user.id,
            status='confirmed'
        )
        db.session.execute(stmt)
        
        db.session.commit()
        flash('Playdate scheduled successfully!')
        return redirect(url_for('view_playdates'))
    
    return render_template('schedule.html', 
                          user_pets=user_pets, 
                          google_maps_api_key=google_maps_api_key)

@app.route('/playdates')
def view_playdates():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # Get upcoming playdates (excluding past ones)
    upcoming_playdates = Playdate.query.filter(
        Playdate.date >= datetime.now()
    ).order_by(Playdate.date).all()
    
    # Get the user's attendance status for each playdate
    playdate_data = []
    for playdate in upcoming_playdates:
        # Check if user is attending this playdate
        attendance = db.session.query(playdate_attendees.c.status).filter(
            playdate_attendees.c.playdate_id == playdate.id,
            playdate_attendees.c.user_id == user.id
        ).first()
        
        # Get all pets for this playdate
        pets = Pet.query.join(playdate_pets).filter(
            playdate_pets.c.playdate_id == playdate.id
        ).all()
        
        playdate_data.append({
            'playdate': playdate,
            'attendance_status': attendance[0] if attendance else None,
            'pets': pets,
            'is_host': playdate.host_id == user.id
        })
    
    return render_template('playdates.html', playdates=playdate_data)

@app.route('/my_pets')
def my_pets():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    if user is None:
        return redirect(url_for('login'))  # Redirect if user is not found
    
    pets = user.pets  # Assuming you have a relationship set up
    return render_template('my_pets.html', pets=pets)

@app.route('/add_pet', methods=['GET', 'POST'])
def add_pet():
    if 'username' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        name = request.form['name']
        species = request.form['species']
        breed = request.form['breed']
        age = request.form['age']
        size = request.form['size']
        temperament = request.form['temperament']
        cropped_image_data = request.form.get('cropped_image')
        if cropped_image_data:
            # Extract the base64 data and save it as an image
            header, encoded = cropped_image_data.split(',', 1)
            image_data = base64.b64decode(encoded)
            image_filename = secure_filename(f"{name}_cropped.jpg")  # Create a unique filename
            with open(os.path.join('static/pet_images', image_filename), 'wb') as f:
                f.write(image_data)
        else:
            image_filename = None  # Handle case where no image is uploaded

        new_pet = Pet(
            name=name,
            species=species,
            breed=breed,
            age=age,
            size=size,
            temperament=temperament,
            owner_id=user.id,
            image_filename=image_filename  # Save the image filename
        )

        try:
            db.session.add(new_pet)
            db.session.commit()
            return redirect(url_for('my_pets'))  # Redirect to My Pets page after adding
        except Exception as e:
            db.session.rollback()
            return render_template('add_pet.html', error=f'Error adding pet: {str(e)}')

    return render_template('add_pet.html')

@app.route('/delete_pet/<int:pet_id>', methods=['POST'])
def delete_pet(pet_id):
    if 'username' not in session:
        return redirect(url_for('login'))

    pet = Pet.query.get(pet_id)
    if pet and pet.owner_id == User.query.filter_by(username=session['username']).first().id:
        try:
            db.session.delete(pet)
            db.session.commit()
            return redirect(url_for('my_pets'))  # Redirect to My Pets page after deletion
        except Exception as e:
            db.session.rollback()
            return render_template('my_pets.html', error=f'Error deleting pet: {str(e)}')

    return redirect(url_for('my_pets'))  # Redirect if pet not found or user not authorized

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    if request.method == 'POST':
        # Handle profile picture upload
        if 'profile_picture' in request.files and request.files['profile_picture'].filename:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to filename to avoid duplicates
                filename = f"{int(time.time())}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], '..', 'profile_pictures', filename))
                user.profile_picture = filename
        
        # Update basic info
        user.bio = request.form.get('bio', '')
        user.location = request.form.get('location', '')
        
        # Update new pet parent fields
        user.pet_owner_since = request.form.get('pet_owner_since', None)
        user.pet_experience_level = request.form.get('pet_experience_level', '')
        
        # Handle checkbox groups
        preferred_meetup_types = request.form.getlist('preferred_meetup_types')
        user.preferred_meetup_types = ','.join(preferred_meetup_types) if preferred_meetup_types else ''
        
        availability = request.form.getlist('availability')
        user.availability = ','.join(availability) if availability else ''
        
        try:
            db.session.commit()
            flash('Profile updated successfully!')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            return render_template('edit_profile.html', user=user, error=f'Error updating profile: {str(e)}', current_year=datetime.now().year)
    
    return render_template('edit_profile.html', user=user, current_year=datetime.now().year)

@app.route('/search', methods=['GET'])
def search():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Check if we have search parameters
    if request.args.get('location'):
        # This is a search request
        location = request.args.get('location')
        distance = int(request.args.get('distance', 25))
        date_str = request.args.get('date')
        sort_by = request.args.get('sort', 'date')
        
        # Get the user's location
        user = User.query.filter_by(username=session['username']).first()
        
        # Get all upcoming playdates
        upcoming_playdates = Playdate.query.filter(Playdate.date > datetime.now()).all()
        
        # Filter by date if provided
        if date_str:
            search_date = datetime.strptime(date_str, '%Y-%m-%d')
            next_day = search_date + timedelta(days=1)
            upcoming_playdates = [p for p in upcoming_playdates if p.date.date() == search_date.date()]
        
        # Calculate distances and filter by distance
        results = []
        for playdate in upcoming_playdates:
            # In a real app, you would calculate the actual distance
            # For now, we'll use a placeholder distance
            # This would typically use geocoding and distance calculation
            distance_value = random.uniform(0.5, 50)  # Random distance for demo
            
            if distance_value <= distance:
                results.append({
                    'playdate': playdate,
                    'distance': distance_value
                })
        
        # Sort results
        if sort_by == 'distance':
            results.sort(key=lambda x: x['distance'])
        else:  # Default sort by date
            results.sort(key=lambda x: x['playdate'].date)
        
        return render_template('search_results.html', 
                              results=results, 
                              sort_by=sort_by,
                              location=location,
                              distance=distance)
    
    # If no search parameters, just show the search form
    return render_template('search.html')

@app.route('/edit_pet/<int:pet_id>', methods=['GET', 'POST'])
def edit_pet(pet_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get the pet from the database
    pet = Pet.query.filter_by(id=pet_id).first()
    
    # Check if pet exists and belongs to the current user
    if not pet or pet.owner_id != User.query.filter_by(username=session['username']).first().id:
        flash('Pet not found or you do not have permission to edit this pet.')
        return redirect(url_for('my_pets'))
    
    if request.method == 'POST':
        # Update pet information
        pet.name = request.form.get('name')
        pet.species = request.form.get('species')
        pet.breed = request.form.get('breed')
        pet.age = request.form.get('age')
        pet.size = request.form.get('size')
        pet.temperament = request.form.get('temperament')
        
        # Handle image upload if provided
        if 'pet_image' in request.files and request.files['pet_image'].filename:
            image = request.files['pet_image']
            if image and allowed_file(image.filename):
                # Generate a secure filename
                filename = secure_filename(f"{pet.id}_{int(time.time())}.jpg")
                # Save the image
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                # Update the pet's image filename
                pet.image_filename = filename
        
        # Save changes to database
        db.session.commit()
        flash('Pet updated successfully!')
        return redirect(url_for('my_pets'))
    
    # For GET request, display the edit form
    return render_template('edit_pet.html', pet=pet)

@app.route('/join_playdate/<int:playdate_id>', methods=['GET', 'POST'])
def join_playdate(playdate_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get(playdate_id)
    
    if not playdate:
        flash('Playdate not found.')
        return redirect(url_for('view_playdates'))
    
    # Get user's pets for selection
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    
    # Check if user is already attending
    attendance = db.session.query(playdate_attendees).filter_by(
        playdate_id=playdate_id, user_id=user.id).first()
    
    current_status = attendance.status if attendance else None
    
    # Get pets already added to this playdate by this user
    user_playdate_pets = []
    if user.pets:
        user_playdate_pets = [pet.id for pet in playdate.pets if pet.owner_id == user.id]
    
    if request.method == 'POST':
        status = request.form.get('status')
        selected_pet_ids = request.form.getlist('selected_pets')
        
        if not status:
            flash('Please select an attendance status.')
            return redirect(url_for('join_playdate', playdate_id=playdate_id))
        
        # Update or add attendance record
        if attendance:
            # Update existing record
            stmt = playdate_attendees.update().\
                where(playdate_attendees.c.playdate_id == playdate_id).\
                where(playdate_attendees.c.user_id == user.id).\
                values(status=status)
            db.session.execute(stmt)
        else:
            # Insert new record
            stmt = playdate_attendees.insert().values(
                playdate_id=playdate_id,
                user_id=user.id,
                status=status
            )
            db.session.execute(stmt)
        
        # Handle pet selection
        # First, remove any existing pets from this user
        for pet in playdate.pets:
            if pet.owner_id == user.id and str(pet.id) not in selected_pet_ids:
                playdate.pets.remove(pet)
        
        # Then add selected pets
        if selected_pet_ids:
            selected_pets = Pet.query.filter(Pet.id.in_(selected_pet_ids)).all()
            for pet in selected_pets:
                if pet not in playdate.pets and pet.owner_id == user.id:
                    playdate.pets.append(pet)
        
        db.session.commit()
        
        flash(f'You have successfully updated your attendance to {status}.')
        return redirect(url_for('view_playdate', playdate_id=playdate_id))
    
    return render_template('join_playdate.html', 
                          playdate=playdate, 
                          user_pets=user_pets,
                          current_status=current_status,
                          selected_pet_ids=user_playdate_pets)

@app.route('/leave_playdate/<int:playdate_id>', methods=['POST'])
def leave_playdate(playdate_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # Delete the attendance record
    stmt = playdate_attendees.delete().where(
        (playdate_attendees.c.playdate_id == playdate_id) & 
        (playdate_attendees.c.user_id == user.id)
    )
    db.session.execute(stmt)
    db.session.commit()
    
    flash('You have left this playdate.')
    return redirect(url_for('view_playdates'))

@app.route('/playdate/<int:playdate_id>')
def view_playdate(playdate_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Get all attendees with their status
    attendees_query = db.session.query(User, playdate_attendees.c.status).join(
        playdate_attendees, User.id == playdate_attendees.c.user_id
    ).filter(playdate_attendees.c.playdate_id == playdate_id).all()
    
    attendees = [{'user': user, 'status': status} for user, status in attendees_query]
    
    # Get all pets attending
    pets = Pet.query.join(playdate_pets).filter(
        playdate_pets.c.playdate_id == playdate_id
    ).all()
    
    # Check if user is attending
    attendance_record = db.session.query(playdate_attendees).filter_by(
        playdate_id=playdate_id, user_id=current_user.id).first()
    
    # Format the date for display
    formatted_date = playdate.date.strftime('%A, %B %d, %Y at %I:%M %p')
    
    return render_template('view_playdate.html', 
                          playdate=playdate, 
                          pets=pets,
                          attendees=attendees,
                          is_host=(playdate.host_id == current_user.id),
                          attendance_status=attendance_record.status if attendance_record else None,
                          formatted_date=formatted_date,
                          current_user=current_user)

@app.route('/edit_playdate/<int:playdate_id>', methods=['GET', 'POST'])
def edit_playdate(playdate_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get(playdate_id)
    
    # Check if playdate exists and user is the host
    if not playdate or playdate.host_id != user.id:
        flash('Playdate not found or you do not have permission to edit it.')
        return redirect(url_for('view_playdates'))
    
    # Get user's pets for the selection
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    
    # Get currently selected pets
    selected_pet_ids = [pet.id for pet in playdate.pets]
    
    # Get Google Maps API key from environment or config
    google_maps_api_key = os.environ.get('GOOGLE_MAPS_API_KEY', app.config.get('GOOGLE_MAPS_API_KEY', ''))
    
    if request.method == 'POST':
        # Update playdate information
        date_str = request.form.get('date')
        location = request.form.get('location')
        description = request.form.get('description')
        new_selected_pet_ids = request.form.getlist('selected_pets')
        
        # Convert date string to datetime object
        date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        
        # Update playdate
        playdate.date = date
        playdate.location = location
        playdate.description = description
        
        # Update selected pets
        if new_selected_pet_ids:
            selected_pets = Pet.query.filter(Pet.id.in_(new_selected_pet_ids)).all()
            playdate.pets = selected_pets
        else:
            playdate.pets = []
        
        db.session.commit()
        flash('Playdate updated successfully!')
        return redirect(url_for('view_playdate', playdate_id=playdate.id))
    
    # Format the date for the datetime-local input
    formatted_date = playdate.date.strftime('%Y-%m-%dT%H:%M')
    
    # For GET request, display the edit form
    return render_template('edit_playdate.html', 
                          playdate=playdate,
                          user_pets=user_pets,
                          selected_pet_ids=selected_pet_ids,
                          formatted_date=formatted_date,
                          google_maps_api_key=google_maps_api_key)

@app.route('/messages')
def messages():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    user = User.query.filter_by(username=session['username']).first()
    conversations = user.get_conversations()
    
    return render_template('messages.html', conversations=conversations, current_user=user)

@app.route('/messages/<int:user_id>', methods=['GET', 'POST'])
def conversation(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    other_user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        content = request.form.get('message')
        if content and content.strip():
            message = Message(
                sender_id=current_user.id,
                recipient_id=user_id,
                content=content
            )
            db.session.add(message)
            db.session.commit()
            
            # Redirect to avoid form resubmission
            return redirect(url_for('conversation', user_id=user_id))
    
    # Mark messages as read
    unread_messages = Message.query.filter_by(
        sender_id=user_id, 
        recipient_id=current_user.id, 
        is_read=False
    ).all()
    
    for message in unread_messages:
        message.is_read = True
    
    db.session.commit()
    
    # Get all messages between the two users
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.recipient_id == user_id)) |
        ((Message.sender_id == user_id) & (Message.recipient_id == current_user.id))
    ).order_by(Message.timestamp).all()
    
    conversations = current_user.get_conversations()
    
    return render_template(
        'conversation.html', 
        messages=messages, 
        other_user=other_user, 
        current_user=current_user,
        conversations=conversations
    )

@app.route('/send_message/<int:user_id>')
def send_message(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    recipient = User.query.get_or_404(user_id)
    
    return redirect(url_for('conversation', user_id=user_id))

@app.route('/profile/<int:user_id>')
def view_profile(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    user = User.query.get_or_404(user_id)
    
    # Don't allow viewing your own profile through this route
    if user.id == current_user.id:
        return redirect(url_for('dashboard'))
    
    return render_template('view_profile.html', user=user, current_user=current_user)

@app.route('/playdate/<int:playdate_id>/chat')
def playdate_group_chat(playdate_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if user is an attendee
    if current_user not in playdate.attendees and current_user.id != playdate.host_id:
        flash('You must be an attendee of this playdate to access the group chat.')
        return redirect(url_for('view_playdate', playdate_id=playdate_id))
    
    # For simplicity, we'll redirect to a special conversation with the host
    # In a real app, you might implement a true group chat feature
    return redirect(url_for('conversation', user_id=playdate.host_id))

@app.route('/write_review/<int:user_id>', methods=['GET', 'POST'])
def write_review(user_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    user_to_review = User.query.get_or_404(user_id)
    
    # Check if the current user can review this user
    if not current_user.can_review_user(user_id):
        flash('You can only review users you have had playdates with.')
        return redirect(url_for('view_profile', user_id=user_id))
    
    # Get shared playdates that haven't been reviewed yet
    shared_playdates = Playdate.query.join(playdate_attendees, Playdate.id == playdate_attendees.c.playdate_id)\
        .filter(playdate_attendees.c.user_id == current_user.id)\
        .filter(Playdate.id.in_(
            db.session.query(playdate_attendees.c.playdate_id)
            .filter(playdate_attendees.c.user_id == user_id)
        ))\
        .filter(Playdate.date < datetime.utcnow())\
        .all()
    
    eligible_playdates = []
    for playdate in shared_playdates:
        existing_review = Review.query.filter_by(
            reviewer_id=current_user.id,
            reviewed_user_id=user_id,
            playdate_id=playdate.id
        ).first()
        
        if not existing_review:
            eligible_playdates.append(playdate)
    
    if request.method == 'POST':
        rating = int(request.form.get('rating'))
        comment = request.form.get('comment')
        playdate_id = request.form.get('playdate_id')
        
        if rating < 1 or rating > 5:
            flash('Rating must be between 1 and 5 stars.')
            return redirect(url_for('write_review', user_id=user_id))
        
        # Create the review
        review = Review(
            reviewer_id=current_user.id,
            reviewed_user_id=user_id,
            playdate_id=playdate_id,
            rating=rating,
            comment=comment
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Your review has been submitted!')
        return redirect(url_for('view_profile', user_id=user_id))
    
    return render_template('write_review.html', 
                          user=user_to_review, 
                          playdates=eligible_playdates)

@app.route('/reviews/<int:user_id>')
def user_reviews(user_id):
    user = User.query.get_or_404(user_id)
    reviews = Review.query.filter_by(reviewed_user_id=user_id).order_by(Review.created_at.desc()).all()
    
    return render_template('user_reviews.html', user=user, reviews=reviews)

@app.route('/playdate/<int:playdate_id>/photos')
def playdate_photos(playdate_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if user is authorized to view this playdate
    if current_user.id != playdate.host_id and current_user not in playdate.attendees:
        flash('You are not authorized to view this playdate.')
        return redirect(url_for('view_playdates'))
    
    # Get all photos for this playdate
    photos = PlaydatePhoto.query.filter_by(playdate_id=playdate_id).order_by(PlaydatePhoto.uploaded_at.desc()).all()
    
    return render_template('playdate_photos.html', 
                          playdate=playdate, 
                          photos=photos, 
                          current_user=current_user)

@app.route('/playdate/<int:playdate_id>/upload_photo', methods=['GET', 'POST'])
def upload_playdate_photo(playdate_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if user is authorized to upload photos to this playdate
    if current_user.id != playdate.host_id and current_user not in playdate.attendees:
        flash('You are not authorized to upload photos to this playdate.')
        return redirect(url_for('view_playdates'))
    
    # Check if the playdate has already happened
    if playdate.date > datetime.utcnow():
        flash('You can only upload photos after the playdate has occurred.')
        return redirect(url_for('view_playdate', playdate_id=playdate_id))
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        photo = request.files['photo']
        caption = request.form.get('caption', '')
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if photo.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if photo and allowed_file(photo.filename, {'png', 'jpg', 'jpeg', 'gif'}):
            # Generate a secure filename
            filename = secure_filename(photo.filename)
            # Add timestamp to ensure uniqueness
            timestamp = int(time.time())
            filename = f"{timestamp}_{filename}"
            
            # Create directory if it doesn't exist
            playdate_photos_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'playdate_photos')
            if not os.path.exists(playdate_photos_dir):
                os.makedirs(playdate_photos_dir)
            
            # Save the file
            photo.save(os.path.join(playdate_photos_dir, filename))
            
            # Create a new PlaydatePhoto record
            new_photo = PlaydatePhoto(
                playdate_id=playdate_id,
                user_id=current_user.id,
                filename=filename,
                caption=caption
            )
            
            db.session.add(new_photo)
            db.session.commit()
            
            flash('Photo uploaded successfully!')
            return redirect(url_for('playdate_photos', playdate_id=playdate_id))
        else:
            flash('Invalid file type. Please upload a PNG, JPG, JPEG, or GIF file.')
    
    return render_template('upload_playdate_photo.html', playdate=playdate)

@app.route('/playdate/photo/<int:photo_id>/delete', methods=['POST'])
def delete_playdate_photo(photo_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    photo = PlaydatePhoto.query.get_or_404(photo_id)
    
    # Check if user is authorized to delete this photo
    if current_user.id != photo.user_id and current_user.id != photo.playdate.host_id:
        flash('You are not authorized to delete this photo.')
        return redirect(url_for('playdate_photos', playdate_id=photo.playdate_id))
    
    # Delete the file from the filesystem
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'playdate_photos', photo.filename))
    except Exception as e:
        # Log the error but continue with database deletion
        print(f"Error deleting file: {e}")
    
    # Delete the database record
    db.session.delete(photo)
    db.session.commit()
    
    flash('Photo deleted successfully!')
    return redirect(url_for('playdate_photos', playdate_id=photo.playdate_id))

@app.route('/gallery')
def public_gallery():
    # Get all public photos, newest first
    photos = GalleryPhoto.query.filter_by(is_public=True).order_by(GalleryPhoto.uploaded_at.desc()).all()
    
    # Get current user if logged in
    current_user = None
    if 'username' in session:
        current_user = User.query.filter_by(username=session['username']).first()
    
    return render_template('public_gallery.html', photos=photos, current_user=current_user)

@app.route('/gallery/upload', methods=['GET', 'POST'])
def upload_gallery_photo():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    
    # Get user's pets for the dropdown
    user_pets = Pet.query.filter_by(owner_id=current_user.id).all()
    
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'photo' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        photo = request.files['photo']
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        pet_id = request.form.get('pet_id')
        is_public = 'is_public' in request.form
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if photo.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if photo and allowed_file(photo.filename, {'png', 'jpg', 'jpeg', 'gif'}):
            # Generate a secure filename
            filename = secure_filename(photo.filename)
            # Add timestamp to ensure uniqueness
            timestamp = int(time.time())
            filename = f"{timestamp}_{filename}"
            
            # Create directory if it doesn't exist
            gallery_photos_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'gallery_photos')
            if not os.path.exists(gallery_photos_dir):
                os.makedirs(gallery_photos_dir)
            
            # Save the file
            photo.save(os.path.join(gallery_photos_dir, filename))
            
            # Create a new GalleryPhoto record
            new_photo = GalleryPhoto(
                user_id=current_user.id,
                pet_id=pet_id if pet_id else None,
                filename=filename,
                title=title,
                description=description,
                is_public=is_public
            )
            
            db.session.add(new_photo)
            db.session.commit()
            
            flash('Photo uploaded successfully!')
            return redirect(url_for('public_gallery'))
        else:
            flash('Invalid file type. Please upload a PNG, JPG, JPEG, or GIF file.')
    
    return render_template('upload_gallery_photo.html', pets=user_pets)

@app.route('/gallery/my-photos')
def my_gallery_photos():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    
    # Get all photos uploaded by the current user
    photos = GalleryPhoto.query.filter_by(user_id=current_user.id).order_by(GalleryPhoto.uploaded_at.desc()).all()
    
    return render_template('my_gallery_photos.html', photos=photos)

@app.route('/gallery/photo/<int:photo_id>')
def view_gallery_photo(photo_id):
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Check if the photo is public or belongs to the current user
    if not photo.is_public and ('username' not in session or 
                               User.query.filter_by(username=session['username']).first().id != photo.user_id):
        flash('You do not have permission to view this photo.')
        return redirect(url_for('public_gallery'))
    
    # Get current user if logged in
    current_user = None
    if 'username' in session:
        current_user = User.query.filter_by(username=session['username']).first()
    
    return render_template('view_gallery_photo.html', photo=photo, current_user=current_user)

@app.route('/gallery/photo/<int:photo_id>/delete', methods=['POST'])
def delete_gallery_photo(photo_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Check if user is authorized to delete this photo
    if current_user.id != photo.user_id:
        flash('You are not authorized to delete this photo.')
        return redirect(url_for('public_gallery'))
    
    # Delete the file from the filesystem
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], 'gallery_photos', photo.filename))
    except Exception as e:
        # Log the error but continue with database deletion
        print(f"Error deleting file: {e}")
    
    # Delete the database record
    db.session.delete(photo)
    db.session.commit()
    
    flash('Photo deleted successfully!')
    return redirect(url_for('my_gallery_photos'))

@app.route('/gallery/photo/<int:photo_id>/toggle-visibility', methods=['POST'])
def toggle_gallery_photo_visibility(photo_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Check if user is authorized to modify this photo
    if current_user.id != photo.user_id:
        flash('You are not authorized to modify this photo.')
        return redirect(url_for('public_gallery'))
    
    # Toggle visibility
    photo.is_public = not photo.is_public
    db.session.commit()
    
    flash(f'Photo is now {"public" if photo.is_public else "private"}.')
    return redirect(url_for('my_gallery_photos'))

# Helper function to check allowed file extensions
def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Create tables if they don't exist
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        # Just log the error and continue
        print(f"Note: {e}")

@app.context_processor
def utility_processor():
    def get_current_user():
        if 'username' in session:
            return User.query.filter_by(username=session['username']).first()
        return None
    
    def now():
        return datetime.utcnow()
    
    return {
        'get_current_user': get_current_user,
        'now': now
    }

if __name__ == '__main__':
    app.run(debug=True)