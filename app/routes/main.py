from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify
from app.models.user import User
from app.models.pet import Pet
from app.models.playdate import Playdate
from app.models.photo import GalleryPhoto
from app.models.associations import playdate_attendees
from app import db
from app.utils.helpers import allowed_file, save_uploaded_file, geocode_address, calculate_distance
import os
from datetime import datetime, timedelta
from sqlalchemy import desc, and_, or_

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    if user is None:
        return redirect(url_for('auth.login'))
    
    # Get user's pets
    pets = Pet.query.filter_by(owner_id=user.id).all()
    
    # Get user's hosted playdates
    hosted_playdates = Playdate.query.filter_by(host_id=user.id).order_by(desc(Playdate.date)).limit(5).all()
    
    # Get playdates where user's pets are participants
    participant_playdates = Playdate.query.join(
        Playdate.pets
    ).filter(
        Pet.owner_id == user.id
    ).order_by(desc(Playdate.date)).limit(5).all()
    
    # Combine and deduplicate
    recent_playdates = list(set(hosted_playdates + participant_playdates))
    recent_playdates.sort(key=lambda x: x.date, reverse=True)
    recent_playdates = recent_playdates[:5]  # Limit to 5 most recent
    
    return render_template(
        'profile.html', 
        user=user, 
        pets=pets,
        playdates=recent_playdates
    )

@bp.route('/user/<int:user_id>')
def view_profile(user_id):
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    # Get the user whose profile is being viewed
    user = User.query.get_or_404(user_id)
    
    # Get user's pets
    pets = Pet.query.filter_by(owner_id=user.id).all()
    
    # Get user's hosted playdates
    hosted_playdates = Playdate.query.filter_by(host_id=user.id).order_by(desc(Playdate.date)).limit(5).all()
    
    # Get playdates where user's pets are participants
    participant_playdates = Playdate.query.join(
        Playdate.pets
    ).filter(
        Pet.owner_id == user.id
    ).order_by(desc(Playdate.date)).limit(5).all()
    
    # Combine and deduplicate
    recent_playdates = list(set(hosted_playdates + participant_playdates))
    recent_playdates.sort(key=lambda x: x.date, reverse=True)
    recent_playdates = recent_playdates[:5]  # Limit to 5 most recent
    
    return render_template(
        'view_profile.html', 
        user=user, 
        pets=pets,
        playdates=recent_playdates
    )

@bp.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    if request.method == 'POST':
        # Update basic information
        user.name = request.form.get('name')
        user.email = request.form.get('email')
        user.bio = request.form.get('bio')
        user.location = request.form.get('location')
        
        # Handle profile picture upload
        if 'profile_picture' in request.files and request.files['profile_picture'].filename:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename, {'jpg', 'jpeg', 'png', 'gif'}):
                filename = save_uploaded_file(
                    file, 
                    'app/static/profile_pictures', 
                    f"user_{user.id}_profile"
                )
                user.profile_picture = filename
        
        try:
            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('main.profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating profile: {str(e)}', 'error')
    
    return render_template('edit_profile.html', user=user)

@bp.route('/gallery')
def gallery():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # Get all gallery photos for the user
    photos = GalleryPhoto.query.filter_by(user_id=user.id).order_by(GalleryPhoto.uploaded_at.desc()).all()
    
    return render_template('gallery.html', photos=photos, user=user)

@bp.route('/gallery/upload', methods=['POST'])
def upload_to_gallery():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    if 'photos' not in request.files:
        flash('No files selected', 'error')
        return redirect(url_for('main.gallery'))
    
    files = request.files.getlist('photos')
    
    for file in files:
        if file and allowed_file(file.filename, {'jpg', 'jpeg', 'png', 'gif'}):
            filename = save_uploaded_file(
                file, 
                'app/static/gallery', 
                f"user_{user.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            
            photo = GalleryPhoto(
                filename=filename,
                user_id=user.id,
                uploaded_at=datetime.now(),
                caption=request.form.get('caption', '')
            )
            db.session.add(photo)
    
    try:
        db.session.commit()
        flash('Photos uploaded successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error uploading photos: {str(e)}', 'error')
    
    return redirect(url_for('main.gallery'))

@bp.route('/gallery/delete/<int:photo_id>', methods=['POST'])
def delete_gallery_photo(photo_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    if photo.user_id != user.id:
        flash('You do not have permission to delete this photo.', 'error')
        return redirect(url_for('main.gallery'))
    
    try:
        # Delete the file from the filesystem
        if photo.filename:
            try:
                file_path = os.path.join('app/static/gallery', photo.filename)
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Error deleting photo file: {e}")
        
        # Delete from database
        db.session.delete(photo)
        db.session.commit()
        flash('Photo deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting photo: {str(e)}', 'error')
    
    return redirect(url_for('main.gallery'))

@bp.route('/search')
def search():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    return render_template('search.html')

@bp.route('/search_results', methods=['GET'])
def search_results():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    # Get search parameters
    location = request.args.get('location')
    distance = request.args.get('distance', '25')  # Default to 25 miles
    date = request.args.get('date')
    
    # Get current user
    current_user = User.query.filter_by(username=session['username']).first()
    
    # Query playdates instead of pets
    query = Playdate.query
    
    # Basic filtering: future playdates only
    query = query.filter(Playdate.date > datetime.now())
    
    # Filter by date if provided
    if date:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
        next_day = date_obj + timedelta(days=1)
        query = query.filter(Playdate.date >= date_obj, Playdate.date < next_day)
    
    # Exclude playdates hosted by the current user and ones they're already attending
    query = query.filter(Playdate.host_id != current_user.id)
    
    # Exclude playdates that the user is already attending
    already_attending_playdate_ids = db.session.query(Playdate.id).\
        join(Playdate.pets).\
        filter(Pet.owner_id == current_user.id).\
        all()
    already_attending_playdate_ids = [p[0] for p in already_attending_playdate_ids]
    
    if already_attending_playdate_ids:
        query = query.filter(~Playdate.id.in_(already_attending_playdate_ids))
    
    # Get all future playdates
    playdates = query.all()
    
    # Format results for the template with distance calculation
    results = []
    
    # If location is provided, filter by distance
    if location:
        # Get coordinates for the search location
        search_lat, search_lng = geocode_address(location)
        
        if search_lat and search_lng:
            # Calculate distance for each playdate and filter based on max distance
            max_distance = float(distance)
            
            for playdate in playdates:
                # Skip playdates without coordinates
                if playdate.latitude is None or playdate.longitude is None:
                    # Fallback to text search for playdates without coordinates
                    if location_matches_text(playdate.location, location):
                        results.append({
                            'playdate': playdate,
                            'distance': None
                        })
                    continue
                
                # Calculate distance between search location and playdate
                dist = calculate_distance(
                    search_lat, search_lng,
                    playdate.latitude, playdate.longitude
                )
                
                # Include playdate if it's within the specified distance
                if dist <= max_distance:
                    results.append({
                        'playdate': playdate,
                        'distance': dist
                    })
        else:
            # Fallback to text search if geocoding fails
            for playdate in playdates:
                if location_matches_text(playdate.location, location):
                    results.append({
                        'playdate': playdate,
                        'distance': None
                    })
    else:
        # If no location provided, include all playdates
        for playdate in playdates:
            results.append({
                'playdate': playdate,
                'distance': None
            })
    
    # Sort results by date (soonest first) by default
    results.sort(key=lambda x: x['playdate'].date)
    
    # If distance data is available, offer option to sort by distance
    has_distance_data = any(r['distance'] is not None for r in results)
    
    # If sort by distance requested and we have distance data, sort
    sort_by = request.args.get('sort_by')
    if sort_by == 'distance' and has_distance_data:
        # Put playdates with distance first, sorted by distance
        with_distance = [r for r in results if r['distance'] is not None]
        without_distance = [r for r in results if r['distance'] is None]
        
        with_distance.sort(key=lambda x: x['distance'])
        results = with_distance + without_distance
    
    return render_template('search_results.html', results=results, sort_by=sort_by)

def location_matches_text(playdate_location, search_location):
    """Helper function to determine if a playdate location matches a search term"""
    # Check if search_location might be a zipcode (5-digit number)
    if search_location.strip().isdigit() and len(search_location.strip()) == 5:
        # For zipcodes, look for addresses containing the zipcode
        return (f" {search_location}" in playdate_location or  # "City, State 12345"
                f"{search_location}-" in playdate_location or  # "12345-6789"
                playdate_location.endswith(search_location))   # ends with zipcode
    else:
        # Standard text search
        return search_location.lower() in playdate_location.lower()

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        # Here you would typically send an email or store the contact message
        # For now, we'll just show a flash message
        flash('Thank you for your message! We will get back to you soon.', 'success')
        return redirect(url_for('main.contact'))
    
    return render_template('contact.html')

@bp.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    username = session['username']
    user = User.query.filter_by(username=username).first()
    
    if not user:
        session.pop('username', None)
        return redirect(url_for('auth.login'))
    
    # Get unread messages count
    unread_messages = user.get_unread_message_count()
    
    # Handle case where user doesn't have the new fields yet
    try:
        # Try to access the new fields
        _ = user.preferred_meetup_types
        _ = user.availability
        _ = user.pet_owner_since
        _ = user.pet_experience_level
    except Exception as e:
        # If there's an error, add the missing columns
        print(f"Error accessing new fields: {e}")
        print("Attempting to update database schema...")
        try:
            # Add the missing columns directly
            with bp.app_context():
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
    
    # Get upcoming playdates for the user
    upcoming_playdates = Playdate.query.filter(
        and_(
            Playdate.date >= datetime.now().date(),
            or_(
                Playdate.host_id == user.id,
                Playdate.pets.any(Pet.owner_id == user.id)
            )
        )
    ).order_by(Playdate.date).limit(5).all()
    
    return render_template('dashboard.html', username=username, user=user, unread_messages=unread_messages, upcoming_playdates=upcoming_playdates)

@bp.route('/resources/safety-guidelines')
def safety_guidelines():
    return render_template('safety_guidelines.html')

@bp.route('/resources/training-resources')
def training_resources():
    return render_template('training_resources.html')

@bp.route('/playdates/view')
def view_playdates():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # Get playdates where the user is either the host or a participant
    host_playdates = Playdate.query.filter_by(host_id=user.id).all()
    
    participant_playdates = Playdate.query.join(
        Playdate.pets
    ).filter(
        Pet.owner_id == user.id
    ).all()
    
    # Combine and deduplicate
    all_playdates = list(set(host_playdates + participant_playdates))
    
    # Sort by date, most recent first
    all_playdates.sort(key=lambda x: x.date, reverse=True)
    
    # Create a list of dictionaries with the structure the template expects
    formatted_playdates = []
    for playdate in all_playdates:
        is_host = playdate.host_id == user.id
        attendance_status = "confirmed" if is_host else "confirmed"  # Default status
        
        # Get pets for this playdate
        pets = playdate.pets
        
        formatted_playdates.append({
            "playdate": playdate,
            "is_host": is_host,
            "attendance_status": attendance_status,
            "pets": pets
        })
    
    return render_template(
        'playdates.html', 
        playdates=formatted_playdates, 
        user=user
    )

@bp.route('/playdates/<int:playdate_id>')
def view_playdate(playdate_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if user is the host or has a pet in the playdate
    is_participant = False
    for pet in playdate.pets:
        if pet.owner_id == user.id:
            is_participant = True
            break
    
    if playdate.host_id != user.id and not is_participant:
        flash('You do not have permission to view this playdate.', 'error')
        return redirect(url_for('main.view_playdates'))
    
    # Get photos for this playdate if they exist
    photos = []
    if hasattr(playdate, 'photos'):
        photos = playdate.photos
    
    # Get the pets attending this playdate
    pets = playdate.pets.all() if hasattr(playdate.pets, 'all') else playdate.pets
    
    # Get attendees with their status
    attendees = []
    if hasattr(playdate, 'attendees'):
        # Query the association table to get status information
        attendees_info = db.session.query(
            User, 
            playdate_attendees.c.status
        ).join(
            playdate_attendees, 
            User.id == playdate_attendees.c.user_id
        ).filter(
            playdate_attendees.c.playdate_id == playdate.id
        ).all()
        
        # Format the data for the template
        attendees = [{'user': user, 'status': status} for user, status in attendees_info]
    
    return render_template(
        'view_playdate.html', 
        playdate=playdate, 
        user=user,
        current_user=user,
        photos=photos,
        pets=pets,
        attendees=attendees,
        is_host=(playdate.host_id == user.id)
    )

@bp.route('/playdates/<int:playdate_id>/join', methods=['GET', 'POST'])
def join_playdate(playdate_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if the user is already the host
    if playdate.host_id == user.id:
        flash('You are the host of this playdate.', 'info')
        return redirect(url_for('main.view_playdate', playdate_id=playdate_id))
    
    # Check if any of the user's pets are already in the playdate
    for pet in playdate.pets:
        if pet.owner_id == user.id:
            flash('You are already participating in this playdate.', 'info')
            return redirect(url_for('main.view_playdate', playdate_id=playdate_id))
    
    # Get user's pets for selection
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    
    if not user_pets:
        flash('You need to add a pet before joining a playdate.', 'error')
        return redirect(url_for('main.view_playdate', playdate_id=playdate_id))
    
    if request.method == 'POST':
        # Get selected pets
        selected_pet_ids = request.form.getlist('selected_pets')
        
        if not selected_pet_ids:
            flash('Please select at least one pet to join the playdate.', 'error')
            return render_template(
                'join_playdate.html',
                playdate=playdate,
                user=user,
                user_pets=user_pets
            )
        
        try:
            # Add selected pets to the playdate
            for pet_id in selected_pet_ids:
                pet = Pet.query.get(pet_id)
                if pet and pet.owner_id == user.id:
                    playdate.pets.append(pet)
            
            db.session.commit()
            flash('Successfully joined the playdate!', 'success')
            return redirect(url_for('main.view_playdate', playdate_id=playdate_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error joining playdate: {str(e)}', 'error')
    
    return render_template(
        'join_playdate.html',
        playdate=playdate,
        user=user,
        user_pets=user_pets
    )

@bp.route('/playdates/<int:playdate_id>/edit', methods=['GET', 'POST'])
def edit_playdate(playdate_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if user is the host
    if playdate.host_id != user.id:
        flash('Only the host can edit a playdate.', 'error')
        return redirect(url_for('main.view_playdate', playdate_id=playdate_id))
    
    # Get user's pets for the selection form
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    
    # Get the current pets selected for this playdate
    selected_pet_ids = [pet.id for pet in playdate.pets]
    
    # Format the date for the datetime-local input
    formatted_date = playdate.date.strftime('%Y-%m-%dT%H:%M')
    
    if request.method == 'POST':
        try:
            # Update playdate information
            playdate.description = request.form.get('description', '')
            playdate.location = request.form.get('location', '')
            
            # Update date and time
            if 'date' in request.form:
                date_str = request.form.get('date')
                playdate.date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
            
            # Update pets
            # Clear current pets
            playdate.pets = []
            
            # Add the selected pets
            selected_pets = request.form.getlist('selected_pets')
            for pet_id in selected_pets:
                pet = Pet.query.get(pet_id)
                if pet and pet.owner_id == user.id:
                    playdate.pets.append(pet)
            
            db.session.commit()
            flash('Playdate updated successfully!', 'success')
            return redirect(url_for('main.view_playdate', playdate_id=playdate.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating playdate: {str(e)}', 'error')
    
    return render_template(
        'edit_playdate.html', 
        playdate=playdate,
        user=user, 
        user_pets=user_pets,
        selected_pet_ids=selected_pet_ids,
        formatted_date=formatted_date,
        google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY', '')
    )

@bp.route('/playdates/<int:playdate_id>/leave', methods=['POST'])
def leave_playdate(playdate_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if user is a participant (not the host)
    is_participant = False
    for pet in playdate.pets:
        if pet.owner_id == user.id and playdate.host_id != user.id:
            is_participant = True
            break
    
    if not is_participant:
        flash('You cannot leave this playdate as you are not a participant.', 'error')
        return redirect(url_for('main.view_playdate', playdate_id=playdate_id))
    
    try:
        # Remove user's pets from the playdate
        for pet in list(playdate.pets):
            if pet.owner_id == user.id:
                playdate.pets.remove(pet)
        
        db.session.commit()
        flash('You have successfully left the playdate.', 'success')
        return redirect(url_for('main.view_playdates'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error leaving playdate: {str(e)}', 'error')
        return redirect(url_for('main.view_playdate', playdate_id=playdate_id)) 