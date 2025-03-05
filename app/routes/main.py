from flask import Blueprint, render_template, redirect, url_for, session, flash, request, jsonify, abort
from app.models.user import User
from app.models.pet import Pet
from app.models.playdate import Playdate
from app.models.gallery_photo import GalleryPhoto
from app.models.review import Review
from app.models.associations import playdate_attendees
from app import db
from app.utils.helpers import allowed_file, save_uploaded_file, geocode_address, calculate_distance
import os
from datetime import datetime, timedelta
from sqlalchemy import desc, and_, or_

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    # Check if user has a mobile preference in their session
    mobile_preference = request.cookies.get('preferMobileVersion')
    
    # Check if it's a mobile device
    user_agent = request.user_agent.string if request.user_agent else ''
    is_mobile = any(device in user_agent for device in ['Android', 'iPhone', 'iPad', 'Mobile', 'webOS'])
    
    # If mobile and no preference set to desktop, redirect to mobile version
    if is_mobile and mobile_preference != 'false':
        return redirect(url_for('main.mobile_index'))
        
    return render_template('index.html')

@bp.route('/mobile')
def mobile_index():
    """Mobile-optimized version of the homepage"""
    return render_template('mobile_index.html')

@bp.route('/profile')
def profile():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    if user is None:
        return redirect(url_for('auth.login'))
    
    # Check if we should display the mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent.lower() for device in ['iphone', 'android', 'mobile', 'tablet'])
    mode = request.args.get('mode', None)  # Check for manual override
    
    # For mobile, redirect to the view_profile route which already has mobile support
    if is_mobile and mode != 'desktop':
        return redirect(url_for('main.view_profile', user_id=user.id))
    
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
    
    # Get the current user's ID for the template
    current_user_id = user.id
    
    return render_template(
        'view_profile.html', 
        user=user, 
        pets=pets,
        playdates=recent_playdates,
        current_user_id=current_user_id
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
    
    # Get the current user's ID for the template to check if viewing own profile
    current_user_id = User.query.filter_by(username=session['username']).first().id
    
    # Check if we should display the mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent.lower() for device in ['iphone', 'android', 'mobile', 'tablet'])
    mode = request.args.get('mode', None)  # Check for manual override
    
    template = 'mobile_view_profile.html' if is_mobile and mode != 'desktop' else 'view_profile.html'
    
    return render_template(
        template, 
        user=user, 
        pets=pets,
        playdates=recent_playdates,
        current_user_id=current_user_id
    )

@bp.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    if user is None:
        flash('User not found.', 'error')
        return redirect(url_for('auth.login'))
    
    if request.method == 'POST':
        # Update basic information
        name = request.form.get('name')
        if name and name.strip():
            user.name = name.strip()
            
        # Only update email if it's provided and not empty
        email = request.form.get('email')
        if email and email.strip():
            user.email = email
            
        # Only update bio if it's provided
        bio = request.form.get('bio')
        if bio is not None:  # Allow empty string to clear the bio
            user.bio = bio
            
        # Only update location if it's provided
        location = request.form.get('location')
        if location is not None:  # Allow empty string to clear the location
            user.location = location
        
        # Update pet parent fields
        user.pet_owner_since = request.form.get('pet_owner_since', None)
        user.pet_experience_level = request.form.get('pet_experience_level', '')
        
        # Handle checkbox groups
        preferred_meetup_types = request.form.getlist('preferred_meetup_types')
        user.preferred_meetup_types = ','.join(preferred_meetup_types) if preferred_meetup_types else ''
        
        availability = request.form.getlist('availability')
        user.availability = ','.join(availability) if availability else ''
        
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
            return render_template('edit_profile.html', 
                                user=user, 
                                error=str(e),
                                current_year=int(datetime.now().year),
                                google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY', ''))
    
    return render_template('edit_profile.html', 
                         user=user,
                         current_year=int(datetime.now().year),
                         google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY', ''))

@bp.route('/gallery')
def gallery():
    if 'username' not in session:
        flash('Please log in to view the gallery', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # If user not found in database, redirect to login
    if user is None:
        flash('User session invalid. Please log in again.', 'error')
        session.clear()  # Clear the invalid session
        return redirect(url_for('auth.login'))
    
    # Get all gallery photos
    photos = GalleryPhoto.query.order_by(GalleryPhoto.created_at.desc()).all()
    
    # Debug first few photos
    print("\nDetailed photo info for first 3 photos:")
    for i, photo in enumerate(photos[:3]):
        print(f"Photo {i+1}:")
        print(f"  - ID: {photo.id}")
        print(f"  - User ID: {photo.user_id} (type: {type(photo.user_id).__name__})")
        print(f"  - Filename: {photo.filename}")
        print(f"  - Is Public: {photo.is_public}")
        print(f"  - Title: {photo.title}")
    
    # Debug info about current user and photo ownership
    print(f"Current user ID: {user.id}")
    print(f"Total photos: {len(photos)}")
    print(f"User's photos: {len([p for p in photos if p.user_id == user.id])}")
    print(f"Public photos: {len([p for p in photos if p.is_public])}")
    print(f"Private photos: {len([p for p in photos if not p.is_public])}")
    print(f"User's private photos: {len([p for p in photos if p.user_id == user.id and not p.is_public])}")
    
    # Print details about each photo in the database
    for photo in photos:
        print(f"Photo ID: {photo.id}, user_id: {photo.user_id}, filename: {photo.filename}, is_public: {photo.is_public}")
    
    # Redirect to new gallery (comment this line if you want to keep using the old gallery)
    return redirect(url_for('main.new_gallery'))
    
    # Uncomment this line if you want to keep using the old gallery
    # return render_template('gallery.html', photos=photos, user=user)

@bp.route('/new-gallery')
def new_gallery():
    """New implementation of the gallery with improved UI and functionality."""
    user = None
    
    # Try to get the user from session username
    if 'username' in session:
        username = session.get('username')
        user = User.query.filter_by(username=username).first()
    
    # If not found, try with user_id
    if user is None and 'user_id' in session:
        user_id = session.get('user_id')
        try:
            user_id_int = int(user_id)
            user = User.query.get(user_id_int)
        except (ValueError, TypeError):
            pass
    
    # Try to find by admin status if needed
    if user is None:
        # Look for admin user as a fallback
        if session.get('is_admin') or 'admin' in session.get('username', '').lower():
            user = User.query.filter_by(is_admin=True).first()
    
    # If no user is found, redirect to login
    if user is None:
        flash('Your session appears to be invalid. Please log in again.', 'error')
        return redirect(url_for('auth.login'))
    
    # Update session with correct user info
    session['username'] = user.username
    session['user_id'] = user.id
    
    # Get all gallery photos
    photos = GalleryPhoto.query.order_by(GalleryPhoto.created_at.desc()).all()
    
    # Render the gallery template
    return render_template('new_gallery.html', photos=photos, user=user)

@bp.route('/gallery/upload', methods=['GET', 'POST'])
def upload_to_gallery():
    if 'username' not in session:
        flash('Please log in to upload photos', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # If user not found in database, redirect to login
    if user is None:
        flash('User session invalid. Please log in again.', 'error')
        session.clear()  # Clear the invalid session
        return redirect(url_for('auth.login'))
    
    # Get user's pets for the form
    pets = Pet.query.filter_by(owner_id=user.id).all()
    
    if request.method == 'POST':
        # Debug print to check what files are being received
        print("Files in request:", request.files)
        print("Form data:", request.form)
        
        # Check if any files were uploaded
        if 'photos[]' not in request.files:
            flash('No files selected', 'error')
            return redirect(request.url)

        files = request.files.getlist('photos[]')
        if not files or not files[0].filename:
            flash('No files selected', 'error')
            return redirect(request.url)

        title = request.form.get('title')
        description = request.form.get('description')
        pet_id = request.form.get('pet_id')
        is_public = request.form.get('is_public') == 'on'
        
        # Ensure the destination directory exists
        upload_dir = 'app/static/pet_images/gallery_photos'
        if not os.path.exists(upload_dir):
            try:
                os.makedirs(upload_dir)
                print(f"Created directory: {upload_dir}")
            except Exception as e:
                print(f"Error creating directory {upload_dir}: {str(e)}")
                flash(f"Error creating upload directory: {str(e)}", 'error')
                return redirect(request.url)
                
        uploaded_count = 0
        for file in files:
            if file and file.filename:  # Check if file has a filename
                try:
                    # Check if file is allowed
                    if not allowed_file(file.filename, {'jpg', 'jpeg', 'png', 'gif'}):
                        flash(f'File {file.filename} has an invalid format. Only JPG, PNG, and GIF are allowed.', 'error')
                        continue

                    # Generate a unique filename
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                    filename = save_uploaded_file(
                        file, 
                        upload_dir, 
                        f"user_{user.id}_{timestamp}"
                    )
                    
                    # Explicitly print the file path and check if it exists
                    file_path = os.path.join(upload_dir, filename)
                    print(f"Saved file to: {file_path}")
                    print(f"File exists: {os.path.exists(file_path)}")
                    
                    # Create a new photo with proper field names
                    photo = GalleryPhoto(
                        filename=filename,
                        user_id=user.id,
                        pet_id=pet_id if pet_id and pet_id.strip() else None,
                        title=title,
                        description=description,
                        is_public=is_public
                    )
                    db.session.add(photo)
                    uploaded_count += 1
                except Exception as e:
                    print(f"Error uploading file {file.filename}:", str(e))  # Debug print
                    flash(f'Error uploading file {file.filename}: {str(e)}', 'error')
                    continue
        
        try:
            if uploaded_count > 0:
                db.session.commit()
                flash(f'Successfully uploaded {uploaded_count} photo{"s" if uploaded_count > 1 else ""}!', 'success')
                return redirect(url_for('main.gallery'))
            else:
                flash('No valid photos were uploaded', 'error')
                return redirect(request.url)
        except Exception as e:
            print("Database error:", str(e))  # Debug print
            db.session.rollback()
            flash(f'Error saving to database: {str(e)}', 'error')
            return redirect(request.url)
    
    return render_template('upload_gallery_photo_new.html', pets=pets)

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
                file_path = os.path.join('app/static/pet_images/gallery_photos', photo.filename)
                print(f"Attempting to delete file: {file_path}")
                print(f"File exists before deletion: {os.path.exists(file_path)}")
                
                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"File deleted successfully: {file_path}")
                else:
                    print(f"Warning: File not found for deletion: {file_path}")
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

@bp.route('/gallery/photo/<int:photo_id>/toggle_visibility', methods=['POST'])
def toggle_gallery_photo_visibility(photo_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Check if user owns the photo
    if photo.user_id != user.id:
        flash('You can only change visibility of your own photos.', 'error')
        return redirect(url_for('main.gallery'))
    
    try:
        # Debug info before change
        print(f"TOGGLE VISIBILITY - Before: Photo ID {photo.id}, is_public: {photo.is_public}, type: {type(photo.is_public)}")
        
        # Toggle the is_public flag - explicitly convert to boolean to avoid type issues
        current_status = bool(photo.is_public)
        photo.is_public = not current_status
        
        # Debug info after change
        print(f"TOGGLE VISIBILITY - After: Photo ID {photo.id}, is_public: {photo.is_public}, type: {type(photo.is_public)}")
        
        # Explicitly flush to ensure the change is registered
        db.session.flush()
        
        # Commit the change
        db.session.commit()
        
        # Verify the change was committed
        db.session.refresh(photo)
        print(f"TOGGLE VISIBILITY - After commit: Photo ID {photo.id}, is_public: {photo.is_public}, type: {type(photo.is_public)}")
        
        flash(f"Photo visibility updated successfully! It is now {'public' if photo.is_public else 'private'}.", 'success')
    except Exception as e:
        db.session.rollback()
        print(f"ERROR in toggle_visibility: {str(e)}")
        flash(f'Error updating photo visibility: {str(e)}', 'error')
    
    return redirect(url_for('main.gallery'))

@bp.route('/gallery/photo/<int:photo_id>/edit', methods=['GET', 'POST'])
def edit_gallery_photo(photo_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Check if user owns the photo
    if photo.user_id != user.id:
        flash('You can only edit your own photos.', 'error')
        return redirect(url_for('main.gallery'))
    
    if request.method == 'POST':
        try:
            photo.title = request.form.get('title')
            photo.description = request.form.get('description')
            photo.pet_id = request.form.get('pet_id') or None
            db.session.commit()
            flash('Photo updated successfully!', 'success')
            return redirect(url_for('main.gallery'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating photo: {str(e)}', 'error')
    
    # Get user's pets for the form
    pets = Pet.query.filter_by(owner_id=user.id).all()
    
    return render_template('edit_gallery_photo.html', photo=photo, pets=pets)

@bp.route('/search')
def search():
    # Check if we should display the mobile version
    user_agent = request.user_agent.string
    is_mobile = any(device in user_agent for device in ['Android', 'iPhone', 'iPad', 'Mobile', 'webOS'])
    mode = request.args.get('mode', None)  # Check for manual override
    
    return render_template('mobile_search.html' if is_mobile and mode != 'desktop' else 'search.html')

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
    
    # Check if we should display the mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent.lower() for device in ['iphone', 'android', 'mobile', 'tablet'])
    mode = request.args.get('mode', None)  # Check for manual override
    
    return render_template('mobile_search_results.html' if is_mobile and mode != 'desktop' else 'search_results.html', 
                          results=results, sort_by=sort_by)

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
    
    # Check if we should display the mobile version
    user_agent = request.user_agent.string if request.user_agent else ''
    is_mobile = any(device in user_agent for device in ['Android', 'iPhone', 'iPad', 'Mobile', 'webOS'])
    mode = request.args.get('mode', None)  # Check for manual override
    
    return render_template(
        'mobile_dashboard.html' if is_mobile and mode != 'desktop' else 'dashboard.html', 
        user=user,  # Pass the User object directly
        unread_messages=unread_messages, 
        upcoming_playdates=upcoming_playdates
    )

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
        
        # Get pets for this playdate
        pets = playdate.pets
        
        formatted_playdates.append({
            "playdate": playdate,
            "is_host": is_host,
            "pets": pets
        })
    
    # Check if we should display the mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    # Check if mode is explicitly specified via query parameter
    mode = request.args.get('mode', None)
    use_mobile = is_mobile and mode != 'desktop'
    
    template = 'mobile_playdates.html' if use_mobile else 'playdates.html'
    
    return render_template(
        template, 
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
    
    attendees = []
    if hasattr(playdate, 'attendees'):
        attendees_info = db.session.query(
            User, 
        ).join(
            playdate_attendees, 
            User.id == playdate_attendees.c.user_id
        ).filter(
            playdate_attendees.c.playdate_id == playdate.id
        ).all()
        
        # Format the data for the template
    
    # Check if the user has already reviewed this playdate
    existing_review = Review.query.filter_by(
        reviewer_id=user.id,
        playdate_id=playdate_id
    ).first()
    
    # Get current datetime for template
    now = datetime.now()
    
    # Check if we should display the mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    # Check if mode is explicitly specified via query parameter
    mode = request.args.get('mode', None)
    use_mobile = is_mobile and mode != 'desktop'
    
    template = 'mobile_view_playdate.html' if use_mobile else 'view_playdate.html'
    
    return render_template(
        template, 
        playdate=playdate, 
        user=user,
        current_user=user,
        photos=photos,
        pets=pets,
        attendees=attendees,
        is_host=(playdate.host_id == user.id),
        now=now,
        user_has_reviewed=existing_review is not None
    )

@bp.route('/playdates/<int:playdate_id>/join', methods=['GET', 'POST'])
def join_playdate(playdate_id):
    if 'username' not in session:
        flash('Please log in to join a playdate.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if the playdate exists
    if not playdate:
        flash('This playdate does not exist.', 'error')
        return redirect(url_for('main.view_playdates'))
    
    # Check if the playdate is in the future
    if playdate.date < datetime.now():
        flash('You cannot join this playdate as it has already occurred.', 'error')
        return redirect(url_for('main.view_playdate', playdate_id=playdate_id))
    
    # Check if the playdate has been cancelled
        flash('You cannot join this playdate as it has been cancelled by the host.', 'error')
        return redirect(url_for('main.view_playdate', playdate_id=playdate_id))
    
    # Check if the user is already the host
    if playdate.host_id == user.id:
        flash('You cannot join this playdate as you are the host.', 'info')
        return redirect(url_for('main.view_playdate', playdate_id=playdate_id))
    
    # Check if any of the user's pets are already in the playdate
    user_participating_pets = [pet for pet in playdate.pets if pet.owner_id == user.id]
    if user_participating_pets:
        pet_names = ', '.join([pet.name for pet in user_participating_pets])
        flash(f'You are already participating in this playdate with your pet(s): {pet_names}.', 'info')
        return redirect(url_for('main.view_playdate', playdate_id=playdate_id))
    
    # Get user's pets for selection
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    
    if not user_pets:
        flash('You need to add at least one pet to your profile before joining a playdate.', 'error')
        return redirect(url_for('pets.add_pet'))
    
    if request.method == 'POST':
        # Get selected pets
        selected_pet_ids = request.form.getlist('selected_pets')
        
        if not selected_pet_ids:
            flash('Please select at least one pet to join the playdate.', 'error')
            
            # Check if we should display the mobile version
            user_agent = request.headers.get('User-Agent', '').lower()
            is_mobile = any(device in user_agent for device in ['iphone', 'android', 'mobile', 'tablet'])
            
            # Check if mode is explicitly specified via query parameter
            mode = request.args.get('mode', None)
            use_mobile = is_mobile and mode != 'desktop'
            
            template = 'mobile_join_playdate.html' if use_mobile else 'join_playdate.html'
            
            return render_template(
                template,
                playdate=playdate,
                user=user,
                user_pets=user_pets
            )
        
        # Check if adding these pets would exceed the maximum
        current_pet_count = len(playdate.pets)
        selected_pets_count = len(selected_pet_ids)
        max_pets = playdate.max_pets if playdate.max_pets is not None else 10  # Default to 10 if None
        if current_pet_count + selected_pets_count > max_pets:
            remaining_spots = max(0, max_pets - current_pet_count)
            if remaining_spots == 0:
                flash(f'Sorry, this playdate is full. The maximum number of pets ({max_pets}) has been reached.', 'error')
            else:
                flash(f'Sorry, you can only add {remaining_spots} more pet(s) to this playdate. You selected {selected_pets_count} pets.', 'error')
            return redirect(url_for('main.view_playdate', playdate_id=playdate_id))
        
        try:
            # Add selected pets to the playdate
            added_pets = []
            for pet_id in selected_pet_ids:
                pet = Pet.query.get(pet_id)
                if pet and pet.owner_id == user.id:
                    playdate.pets.append(pet)
                    added_pets.append(pet.name)
            
            # Add the user to the attendees list if not already there
            if user not in playdate.attendees:
                playdate.attendees.append(user)
            
            db.session.commit()
            pet_names = ', '.join(added_pets)
            flash(f'Successfully joined the playdate with {pet_names}!', 'success')
            return redirect(url_for('main.view_playdate', playdate_id=playdate_id))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred while joining the playdate: {str(e)}', 'error')
    
    # Check if we should display the mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    # Check if mode is explicitly specified via query parameter
    mode = request.args.get('mode', None)
    use_mobile = is_mobile and mode != 'desktop'
    
    template = 'mobile_join_playdate.html' if use_mobile else 'join_playdate.html'
    
    return render_template(
        template,
        playdate=playdate,
        user=user,
        user_pets=user_pets
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
        
        # Remove user from attendees list
        if user in playdate.attendees:
            playdate.attendees.remove(user)
        
        db.session.commit()
        flash('You have successfully left the playdate.', 'success')
        return redirect(url_for('main.view_playdates'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error leaving playdate: {str(e)}', 'error')
        return redirect(url_for('main.view_playdate', playdate_id=playdate_id)) 