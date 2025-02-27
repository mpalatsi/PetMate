from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import base64
import time
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///petmate.db'
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Required for session management
app.config['GOOGLE_MAPS_API_KEY'] = os.environ.get('GOOGLE_MAPS_API_KEY', 'YOUR_DEFAULT_API_KEY')
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
    profile_picture = db.Column(db.String(255))  # New field for profile picture
    bio = db.Column(db.Text)  # New field for user bio
    location = db.Column(db.String(200))  # Add this line for location

    # Define the relationship to the Pet model
    pets = db.relationship('Pet', backref='owner', lazy=True)

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
    
    user = User.query.filter_by(username=session['username']).first()
    
    # Pass the user object to the template
    return render_template('dashboard.html', username=user.username, email=user.email, user=user)

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
    
    if request.method == 'POST':
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
        
        db.session.add(playdate)
        db.session.commit()
        
        flash('Playdate scheduled successfully!')
        return redirect(url_for('view_playdates'))
    
    return render_template('schedule.html', user_pets=user_pets)

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
        user.bio = request.form.get('bio')
        user.location = request.form.get('location')
        profile_picture_file = request.files.get('profile_picture')
        
        if profile_picture_file:
            # Create the directory if it doesn't exist
            profile_pictures_dir = os.path.join('static', 'profile_pictures')
            if not os.path.exists(profile_pictures_dir):
                os.makedirs(profile_pictures_dir)

            profile_picture_filename = secure_filename(profile_picture_file.filename)
            profile_picture_file.save(os.path.join(profile_pictures_dir, profile_picture_filename))
            user.profile_picture = profile_picture_filename

        try:
            db.session.commit()
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            return render_template('edit_profile.html', user=user, error=f'Error updating profile: {str(e)}')

    return render_template('edit_profile.html', user=user)

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

@app.route('/view_playdate/<int:playdate_id>')
def view_playdate(playdate_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    playdate = Playdate.query.get(playdate_id)
    if not playdate:
        flash('Playdate not found.')
        return redirect(url_for('view_playdates'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # Check if user is attending
    attendance_record = db.session.query(playdate_attendees).filter_by(
        playdate_id=playdate_id, user_id=user.id).first()
    
    # Get all attendees with their status
    attendees_query = db.session.query(User, playdate_attendees.c.status).join(
        playdate_attendees, User.id == playdate_attendees.c.user_id
    ).filter(playdate_attendees.c.playdate_id == playdate_id).all()
    
    attendees = [{'user': user, 'status': status} for user, status in attendees_query]
    
    # Get all pets attending
    pets = Pet.query.join(playdate_pets).filter(
        playdate_pets.c.playdate_id == playdate_id
    ).all()
    
    return render_template('view_playdate.html', 
                          playdate=playdate,
                          pets=pets,
                          attendees=attendees,
                          is_host=(playdate.host_id == user.id),
                          attendance_status=attendance_record.status if attendance_record else None)

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
                          formatted_date=formatted_date)

# Create tables if they don't exist
with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        # Just log the error and continue
        print(f"Note: {e}")

if __name__ == '__main__':
    app.run(debug=True)