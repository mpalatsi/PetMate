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
from app.models.message import Message
from flask_login import login_required, current_user
from app.models.photo_like import PhotoLike
from app.models.photo_comment import PhotoComment
from app.models.photo_report import PhotoReport
from app.routes.gallery import PhotoUploadForm

bp = Blueprint('main', __name__)

# Helper function to detect mobile devices
def is_mobile_device(request):
    user_agent = request.headers.get('User-Agent', '').lower()
    return any(device in user_agent.lower() for device in ['iphone', 'android', 'mobile', 'tablet'])

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
    is_mobile = is_mobile_device(request)
    mode = request.args.get('mode', '')
    
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
    current_user_id = User.query.filter_by(username=session['username']).first().id if 'username' in session else None
    
    # Check if we should display the mobile version
    is_mobile = is_mobile_device(request)
    mode = request.args.get('mode', '')
    
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
    
    # Check if the user is on a mobile device
    is_mobile = is_mobile_device(request)
    mode = request.args.get('mode', '')
    
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
                    'static/profile_pictures', 
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
            template = 'mobile_edit_profile.html' if is_mobile and mode != 'desktop' else 'edit_profile.html'
            return render_template(template, 
                                user=user, 
                                error=str(e),
                                current_year=int(datetime.now().year),
                                google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY', ''))
    
    # Select the appropriate template based on device
    template = 'mobile_edit_profile.html' if is_mobile and mode != 'desktop' else 'edit_profile.html'
    
    return render_template(template, 
                         user=user,
                         current_year=int(datetime.now().year),
                         google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY', ''))

@bp.route('/upload-to-gallery', methods=['GET', 'POST'])
def upload_to_gallery():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    pets = Pet.query.filter_by(owner_id=user.id).all()
    
    # Create a photo form for the template
    form = PhotoUploadForm()
    form.pet_id.choices = [(0, 'None')] + [(pet.id, pet.name) for pet in pets]
    
    if request.method == 'POST':
        try:
            # Process form submission
            pass  # Placeholder for form processing code
        except Exception as e:
            print("Database error:", str(e))  # Debug print
            db.session.rollback()
            flash(f'Error saving to database: {str(e)}', 'error')
            return redirect(request.url)
    
    # Check if mobile using the shared function
    is_mobile = is_mobile_device(request)
    
    # Don't use templates from this route - redirect to the appropriate gallery route
    # This avoids duplicating logic and prevents template errors
    if is_mobile:
        return redirect(url_for('gallery.mobile_upload_photo'))
    else:
        return redirect(url_for('gallery.upload_photo'))

@bp.route('/gallery/delete/<int:photo_id>', methods=['POST'])
def delete_gallery_photo(photo_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    if photo.user_id != user.id:
        flash('You do not have permission to delete this photo.', 'error')
        return redirect(url_for('gallery.index'))
    
    try:
        # Delete the file from the filesystem
        if photo.filename:
            try:
                file_path = os.path.join('static/pet_images/gallery_photos', photo.filename)
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
    
    return redirect(url_for('gallery.index'))

@bp.route('/gallery/photo/<int:photo_id>/toggle_visibility', methods=['POST'])
def toggle_gallery_photo_visibility(photo_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Check if user owns the photo
    if photo.user_id != user.id:
        flash('You can only change visibility of your own photos.', 'error')
        return redirect(url_for('gallery.index'))
    
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
        
        status = 'public' if photo.is_public else 'private'
        flash(f"Photo visibility updated successfully! It is now {status}.", 'success')
    except Exception as e:
        db.session.rollback()
        print(f"ERROR in toggle_visibility: {str(e)}")
        flash(f'Error updating photo visibility: {str(e)}', 'error')
    
    return redirect(url_for('gallery.index'))

@bp.route('/gallery/photo/<int:photo_id>/edit', methods=['GET', 'POST'])
def edit_gallery_photo(photo_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Check if user owns the photo
    if photo.user_id != user.id:
        flash('You can only edit your own photos.', 'error')
        return redirect(url_for('gallery.index'))
    
    if request.method == 'POST':
        try:
            photo.title = request.form.get('title')
            photo.description = request.form.get('description')
            photo.pet_id = request.form.get('pet_id') or None
            photo.is_public = 'is_public' in request.form
            db.session.commit()
            flash('Photo updated successfully!', 'success')
            return redirect(url_for('main.view_gallery_photo', photo_id=photo.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating photo: {str(e)}', 'error')
    
    # Get user's pets for the form
    pets = Pet.query.filter_by(owner_id=user.id).all()
    
    # Check if we should display mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent.lower() for device in ['iphone', 'android', 'mobile', 'tablet'])
    mode = request.args.get('mode', None)  # Check for manual override
    
    # Choose template based on device type
    template = 'mobile_edit_gallery_photo.html' if is_mobile and mode != 'desktop' else 'edit_gallery_photo.html'
    
    return render_template(template, photo=photo, pets=pets, user=user)

@bp.route('/gallery/photo/<int:photo_id>')
def view_gallery_photo(photo_id):
    """View a single gallery photo."""
    if 'username' not in session:
        flash('Please log in to view this photo', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # Get the photo
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Check if the user has permission to view this photo
    if not photo.is_public and photo.user_id != user.id:
        flash('You do not have permission to view this photo', 'error')
        return redirect(url_for('gallery.index'))
    
    # Check if we should display the mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent.lower() for device in ['iphone', 'android', 'mobile', 'tablet'])
    mode = request.args.get('mode', None)  # Check for manual override
    
    # Choose template based on device type
    template = 'mobile_view_gallery_photo.html' if is_mobile and mode != 'desktop' else 'view_gallery_photo.html'
    
    # Get user's like status
    user_like = PhotoLike.query.filter_by(user_id=user.id, photo_id=photo_id).first()
    
    # Get comments for the photo
    comments = PhotoComment.query.filter_by(photo_id=photo_id).order_by(PhotoComment.created_at.desc()).all()
    
    return render_template(template, photo=photo, current_user=user, user_like=user_like, comments=comments)

@bp.route('/gallery/photo/<int:photo_id>/like', methods=['POST'])
def like_gallery_photo(photo_id):
    """Like a gallery photo."""
    if 'username' not in session:
        flash('Please log in to like photos', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # Get the photo
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Check if the user already liked the photo
    existing_like = PhotoLike.query.filter_by(user_id=user.id, photo_id=photo_id).first()
    
    if existing_like:
        # Unlike the photo
        db.session.delete(existing_like)
        flash('Photo unliked!', 'success')
    else:
        # Like the photo
        like = PhotoLike(user_id=user.id, photo_id=photo_id)
        db.session.add(like)
        flash('Photo liked!', 'success')
    
    db.session.commit()
    
    # Return to photo view
    return redirect(url_for('main.view_gallery_photo', photo_id=photo_id))

@bp.route('/gallery/photo/<int:photo_id>/comment', methods=['POST'])
def comment_gallery_photo(photo_id):
    """Add a comment to a gallery photo."""
    if 'username' not in session:
        flash('Please log in to comment on photos', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # Get the photo
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Get the comment
    comment_text = request.form.get('comment', '').strip()
    
    if not comment_text:
        flash('Comment cannot be empty', 'error')
    else:
        # Add the comment
        comment = PhotoComment(user_id=user.id, photo_id=photo_id, comment=comment_text)
        db.session.add(comment)
        db.session.commit()
        flash('Comment added!', 'success')
    
    # Return to photo view
    return redirect(url_for('main.view_gallery_photo', photo_id=photo_id))

@bp.route('/gallery/photo/<int:photo_id>/comment/<int:comment_id>/delete', methods=['POST'])
def delete_gallery_photo_comment(photo_id, comment_id):
    """Delete a comment from a gallery photo."""
    if 'username' not in session:
        flash('Please log in to delete comments', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # Get the comment
    comment = PhotoComment.query.get_or_404(comment_id)
    
    # Check if the user is authorized to delete the comment
    if comment.user_id != user.id and comment.photo.user_id != user.id:
        flash('You are not authorized to delete this comment', 'error')
    else:
        db.session.delete(comment)
        db.session.commit()
        flash('Comment deleted!', 'success')
    
    # Return to photo view
    return redirect(url_for('main.view_gallery_photo', photo_id=photo_id))

@bp.route('/gallery/photo/<int:photo_id>/report', methods=['GET', 'POST'])
def report_gallery_photo(photo_id):
    """Report a gallery photo."""
    if 'username' not in session:
        flash('Please log in to report photos', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # Get the photo
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    if request.method == 'POST':
        # Check if the user already reported the photo
        existing_report = PhotoReport.query.filter_by(user_id=user.id, photo_id=photo_id).first()
        
        if existing_report:
            flash('You have already reported this photo', 'error')
        else:
            # Get report data
            reason = request.form.get('reason', '').strip()
            details = request.form.get('details', '').strip()
            
            if not reason:
                flash('Please select a reason for reporting', 'error')
            else:
                # Create the report
                report = PhotoReport(
                    user_id=user.id,
                    photo_id=photo_id,
                    reason=reason,
                    details=details
                )
                db.session.add(report)
                db.session.commit()
                flash('Thank you for your report. Our team will review it shortly.', 'success')
                return redirect(url_for('gallery.index'))
    
    # Check if we should display the mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent.lower() for device in ['iphone', 'android', 'mobile', 'tablet'])
    mode = request.args.get('mode', None)  # Check for manual override
    
    # Choose template based on device type
    template = 'mobile_report_photo.html' if is_mobile and mode != 'desktop' else 'report_photo.html'
    
    return render_template(template, photo=photo, current_user=user)

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
@login_required
def dashboard():
    # Get user agent and mode
    user_agent = request.headers.get('User-Agent', '')
    mode = request.args.get('mode', '')
    
    # Check if mobile device based on user agent
    is_mobile = any(device in user_agent.lower() for device in ['iphone', 'android', 'mobile'])
    
    # Debug prints
    print(f"User-Agent: {user_agent}")
    print(f"Is Mobile: {is_mobile}")
    print(f"Mode: {mode}")
    
    # Determine which template to use
    if mode == 'desktop':
        template = 'dashboard.html'
    elif mode == 'mobile':
        template = 'mobile_dashboard.html'
    elif mode == 'test':
        template = 'mobile_dashboard_test3.html'
    else:
        # Default behavior based on device type
        template = 'mobile_dashboard.html' if is_mobile else 'dashboard.html'
    
    print(f"Selected Template: {template}")
    
    # Get user data
    user = current_user
    user_id = user.id
    
    # Get unread messages count
    unread_messages = Message.query.filter_by(recipient_id=user_id, is_read=False).count()
    
    # Get upcoming playdates
    upcoming_playdates = Playdate.query.filter(
        or_(
            Playdate.host_id == user_id,
            Playdate.attendees.any(id=user_id)
        ),
        Playdate.status == 'accepted',
        Playdate.date >= datetime.now()
    ).order_by(Playdate.date).all()
    
    # Get user's pets
    pets = Pet.query.filter_by(owner_id=user_id).all()
    
    # Pass additional debug info to template
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return render_template(
        template,
        user=user,
        pets=pets,
        unread_messages=unread_messages,
        upcoming_playdates=upcoming_playdates,
        user_agent=user_agent,
        now=now
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

@bp.route('/debug_user')
def debug_user():
    """Debug route to show user and admin status information"""
    data = {
        'is_authenticated': False,
        'username': None,
        'is_admin': False,
        'admin_type': None,
        'session_username': session.get('username', 'Not in session'),
        'session_keys': list(session.keys())
    }
    
    if hasattr(current_user, 'is_authenticated'):
        data['is_authenticated'] = current_user.is_authenticated
    
    if hasattr(current_user, 'username'):
        data['username'] = current_user.username
    
    if hasattr(current_user, 'is_admin'):
        data['is_admin'] = current_user.is_admin
        data['admin_type'] = type(current_user.is_admin).__name__
    
    # Return as both HTML and JSON for easy access
    if request.args.get('format') == 'json':
        return jsonify(data)
    
    return f"""
    <html>
        <head><title>User Debug</title></head>
        <body>
            <h1>User Debug Info</h1>
            <pre>{str(data)}</pre>
            <h2>Current User Object</h2>
            <pre>{str(current_user.__dict__)}</pre>
            <div style="margin-top: 20px;">
                <a href="/admin/" style="display: inline-block; padding: 10px 20px; background-color: #ff5722; color: white; text-decoration: none; border-radius: 5px;">Go to Admin Panel Directly</a>
            </div>
        </body>
    </html>
    """

@bp.route('/gallery-redesigned')
def gallery_redesigned():
    """Redirects to the enhanced gallery implementation"""
    return redirect(url_for('gallery.index'))

# Original implementation commented out
# def gallery_redesigned():
#     """Completely redesigned gallery page."""
#     user = None
#     
#     # Try to get the user from session username
#     if 'username' in session:
#         username = session.get('username')
#         user = User.query.filter_by(username=username).first()
#     
#     # If not found, try with user_id
#     if user is None and 'user_id' in session:
#         user_id = session.get('user_id')
#         try:
#             user_id_int = int(user_id)
#             user = User.query.get(user_id_int)
#         except (ValueError, TypeError):
#             pass
#     
#     # If no user is found, redirect to login
#     if user is None:
#         flash('Please log in to view this page', 'error')
#         return redirect(url_for('auth.login'))
#     
#     # Fetch all photos (visible to this user)
#     all_photos = []
#     
#     # Personal photos (owned by the user)
#     personal_photos = GalleryPhoto.query.filter_by(user_id=user.id).order_by(GalleryPhoto.created_at.desc()).all()
#     
#     # Public photos (visible to everyone)
#     public_photos = GalleryPhoto.query.filter_by(is_public=True).order_by(GalleryPhoto.created_at.desc()).all()
#     
#     # Combine and deduplicate photos
#     all_photos = personal_photos.copy()
#     for photo in public_photos:
#         if photo not in all_photos:
#             all_photos.append(photo)
#     
#     # Sort combined photos by upload date (newest first)
#     all_photos.sort(key=lambda x: x.created_at, reverse=True)
#     
#     return render_template('gallery_redesigned.html', 
#                            all_photos=all_photos,
#                            user=user) 