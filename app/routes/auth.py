from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from app.models.user import User
from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from app.utils.helpers import allowed_file, save_uploaded_file
from werkzeug.utils import secure_filename
import os
import time
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    print("Register route called with method:", request.method)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        name = request.form.get('name', username)  # Use get() with a default value of username
        
        print(f"Registration attempt: username={username}, email={email}")
        
        # Check if username already exists
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            return render_template('register.html')
        
        # Check if email already exists
        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash('Email already registered. Please use a different email or login.', 'error')
            return render_template('register.html')
        
        # Handle profile picture upload
        profile_picture = None
        if 'profile_picture' in request.files and request.files['profile_picture'].filename:
            file = request.files['profile_picture']
            print(f"Profile picture uploaded: {file.filename}")
            if file and allowed_file(file.filename, {'jpg', 'jpeg', 'png', 'gif'}):
                # We don't have the user ID yet, so we'll use the username for now
                profile_picture = save_uploaded_file(
                    file, 
                    'app/static/profile_pictures', 
                    f"{username}_profile"
                )
        
        # Create a new user object
        new_user = User(
            username=username,
            password=generate_password_hash(password),
            email=email,
            profile_picture=profile_picture
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            # Debug information
            print(f"User created successfully: {username} with ID: {new_user.id}")
            flash(f"Created user: {username} with ID: {new_user.id}", 'info')
            
            # If we saved a profile picture with the username, rename it with the user ID
            if profile_picture:
                # Get the file extension
                _, ext = os.path.splitext(profile_picture)
                
                # Old and new paths
                old_path = os.path.join('app/static/profile_pictures', profile_picture)
                new_filename = f"user_{new_user.id}_profile{ext}"
                new_path = os.path.join('app/static/profile_pictures', new_filename)
                
                # Rename the file
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                    
                    # Update the user record
                    new_user.profile_picture = new_filename
                    db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            print(f"Error during registration: {str(e)}")
            flash(f'Error during registration: {str(e)}', 'error')
    
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    print("Login route called with method:", request.method)
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        print(f"Login attempt: username={username}")

        user = User.query.filter_by(username=username).first()
        
        if user:
            # Debug information
            print(f"Found user: {username}")
            flash(f"Found user: {username}", 'info')
            
            is_password_valid = check_password_hash(user.password, password)
            print(f"Password valid: {is_password_valid}")
            flash(f"Password valid: {is_password_valid}", 'info')
            
            if is_password_valid:
                session['username'] = username
                session['user_id'] = user.id
                flash('Login successful!', 'success')
                print(f"Login successful for: {username}")
                return redirect(url_for('main.index'))
            else:
                print(f"Invalid password for: {username}")
                flash('Invalid password.', 'error')
        else:
            print(f"No user found with username: {username}")
            flash(f"No user found with username: {username}", 'error')

    return render_template('login.html')

@bp.route('/logout')
def logout():
    session.pop('username', None)
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        
        if user:
            # In a real application, you would generate a token and send an email
            # For now, we'll just show a flash message
            flash('Password reset instructions have been sent to your email.', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('Email not found.', 'error')
    
    return render_template('reset_password_request.html')

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # In a real application, you would validate the token
    # For now, we'll just show the form
    
    if request.method == 'POST':
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('reset_password.html', token=token)
        
        # In a real application, you would find the user associated with the token
        # and update their password
        flash('Your password has been reset successfully. Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', token=token)

@bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    if request.method == 'POST':
        current_password = request.form['current_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        
        if not check_password_hash(user.password, current_password):
            flash('Current password is incorrect.', 'error')
            return render_template('change_password.html')
        
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('change_password.html')
        
        user.password = generate_password_hash(new_password)
        db.session.commit()
        
        flash('Password changed successfully.', 'success')
        return redirect(url_for('main.profile'))
    
    return render_template('change_password.html')

@bp.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    if request.method == 'POST':
        # Handle profile picture upload
        if 'profile_picture' in request.files and request.files['profile_picture'].filename:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to filename to avoid duplicates
                filename = f"{int(time.time())}_{filename}"
                file.save(os.path.join('app/static/profile_pictures', filename))
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
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            return render_template('edit_profile.html', user=user, error=f'Error updating profile: {str(e)}', current_year=datetime.now().year)
    
    return render_template('edit_profile.html', user=user, current_year=datetime.now().year)

# Helper function to check allowed file extensions
def allowed_file(filename, allowed_extensions={'png', 'jpg', 'jpeg', 'gif'}):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

# Debug route to check session data
@bp.route('/debug_session')
def debug_session():
    session_data = dict(session)
    return render_template('debug_session.html', session_data=session_data, get_user=get_user)
    
def get_user(username):
    """Helper function to get a user by username"""
    return User.query.filter_by(username=username).first() 