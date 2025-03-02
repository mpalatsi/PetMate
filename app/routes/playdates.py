from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify
from app.models.user import User
from app.models.pet import Pet
from app.models.playdate import Playdate
from app.models.photo import PlaydatePhoto
from app.models.playdate_message import PlaydateMessage
from app import db
from app.utils.helpers import allowed_file, save_uploaded_file, geocode_address
from sqlalchemy import or_, and_
import os
from datetime import datetime

bp = Blueprint('playdates', __name__, url_prefix='/playdates')

@bp.route('/')
def playdates():
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
    
    # Format playdates for the template
    formatted_playdates = []
    for playdate in all_playdates:
        is_host = playdate.host_id == user.id
        formatted_playdates.append({
            "playdate": playdate,
            "is_host": is_host,
            "attendance_status": "confirmed",
            "pets": playdate.pets
        })
    
    # Check if the request is from a mobile device
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

@bp.route('/create', methods=['GET', 'POST'])
def create_playdate():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    
    if request.method == 'POST':
        try:
            description = request.form['description']
            location = request.form['location']
            date_str = request.form['date']
            time_str = request.form['time']
            
            # Combine date and time
            date_time_str = f"{date_str} {time_str}"
            date_time = datetime.strptime(date_time_str, '%Y-%m-%d %H:%M')
            
            # Get the selected pets
            pet_ids = request.form.getlist('pet_ids')
            
            if not pet_ids:
                flash('Please select at least one pet for the playdate.', 'error')
                # Check if we should display the mobile version
                user_agent = request.user_agent.string
                is_mobile = any(device in user_agent for device in ['Android', 'iPhone', 'iPad', 'Mobile', 'webOS'])
                mode = request.args.get('mode', None)  # Check for manual override
                
                return render_template(
                    'mobile_create_playdate.html' if is_mobile and mode != 'desktop' else 'create_playdate.html', 
                    user=user, 
                    user_pets=user_pets
                )
            
            # Create a new playdate
            new_playdate = Playdate(
                description=description,
                location=location,
                date=date_time,
                host_id=user.id
            )
            
            # Geocode the location
            lat, lng = geocode_address(location)
            if lat and lng:
                new_playdate.latitude = lat
                new_playdate.longitude = lng
            
            db.session.add(new_playdate)
            db.session.flush()  # Get the ID without committing
            
            # Add the selected pets to the playdate
            for pet_id in pet_ids:
                pet = Pet.query.get(pet_id)
                if pet and pet.owner_id == user.id:
                    new_playdate.pets.append(pet)
            
            db.session.commit()
            flash('Playdate created successfully!', 'success')
            return redirect(url_for('playdates.view_playdate', playdate_id=new_playdate.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating playdate: {str(e)}', 'error')
            print(f"Error creating playdate: {str(e)}")
            
            # Check if we should display the mobile version
            user_agent = request.user_agent.string
            is_mobile = any(device in user_agent for device in ['Android', 'iPhone', 'iPad', 'Mobile', 'webOS'])
            mode = request.args.get('mode', None)  # Check for manual override
            
            return render_template(
                'mobile_create_playdate.html' if is_mobile and mode != 'desktop' else 'create_playdate.html', 
                user=user, 
                user_pets=user_pets
            )
    
    # Check if we should display the mobile version
    user_agent = request.user_agent.string
    is_mobile = any(device in user_agent for device in ['Android', 'iPhone', 'iPad', 'Mobile', 'webOS'])
    mode = request.args.get('mode', None)  # Check for manual override
    
    return render_template(
        'mobile_create_playdate.html' if is_mobile and mode != 'desktop' else 'create_playdate.html', 
        user=user, 
        user_pets=user_pets, 
        google_maps_api_key=os.environ.get('GOOGLE_MAPS_API_KEY', '')
    )

@bp.route('/<int:playdate_id>')
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
        return redirect(url_for('playdates.playdates'))
    
    # Get photos for this playdate
    photos = PlaydatePhoto.query.filter_by(playdate_id=playdate_id).all()
    
    # Check if the request is from a mobile device
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    # Check if mode is explicitly specified via query parameter
    mode = request.args.get('mode', None)
    use_mobile = is_mobile and mode != 'desktop'
    
    # Get all attendees for the playdate
    attendees = []
    for pet in playdate.pets:
        pet_owner = pet.owner
        if pet_owner.id not in [attendee_info['user'].id for attendee_info in attendees]:
            attendees.append({
                'user': pet_owner,
                'status': 'confirmed'  # Default status, can be customized
            })
    
    template = 'mobile_view_playdate.html' if use_mobile else 'view_playdate.html'
    return render_template(
        template,
        playdate=playdate, 
        user=user,
        photos=photos,
        pets=playdate.pets,
        attendees=attendees,
        is_host=(playdate.host_id == user.id)
    )

@bp.route('/<int:playdate_id>/add_photos', methods=['POST'])
def add_photos(playdate_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Verify user is participant or host
    is_participant = False
    for pet in playdate.pets:
        if pet.owner_id == user.id:
            is_participant = True
            break
    
    if playdate.host_id != user.id and not is_participant:
        flash('You do not have permission to add photos to this playdate.', 'error')
        return redirect(url_for('playdates.playdates'))
    
    # Handle the uploaded photos
    if 'photos' not in request.files:
        flash('No files selected', 'error')
        return redirect(url_for('playdates.playdate_photos', playdate_id=playdate_id))
    
    files = request.files.getlist('photos')
    
    for file in files:
        if file and allowed_file(file.filename, {'jpg', 'jpeg', 'png', 'gif'}):
            filename = save_uploaded_file(
                file, 
                'app/static/playdate_photos', 
                f"playdate_{playdate_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            
            photo = PlaydatePhoto(
                filename=filename,
                user_id=user.id,
                playdate_id=playdate_id
            )
            db.session.add(photo)
    
    try:
        db.session.commit()
        flash('Photos uploaded successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error uploading photos: {str(e)}', 'error')
    
    return redirect(url_for('playdates.playdate_photos', playdate_id=playdate_id))

@bp.route('/<int:playdate_id>/cancel', methods=['POST'])
def cancel_playdate(playdate_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Only the host can cancel
    if playdate.host_id != user.id:
        flash('Only the host can cancel a playdate.', 'error')
        return redirect(url_for('playdates.view_playdate', playdate_id=playdate_id))
    
    try:
        playdate.status = 'cancelled'
        db.session.commit()
        flash('Playdate cancelled successfully.', 'success')
        return redirect(url_for('playdates.playdates'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error cancelling playdate: {str(e)}', 'error')
        return redirect(url_for('playdates.view_playdate', playdate_id=playdate_id))

@bp.route('/<int:playdate_id>/photos')
def playdate_photos(playdate_id):
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
        flash('You do not have permission to view this playdate gallery.', 'error')
        return redirect(url_for('playdates.playdates'))
    
    # Get photos for this playdate
    photos = PlaydatePhoto.query.filter_by(playdate_id=playdate_id).all()
    
    # Make sure current_user is explicitly defined and available in the template
    current_user = user
    
    # Define get_current_user function for the template
    def get_current_user():
        return user
    
    return render_template(
        'playdate_photos.html', 
        playdate=playdate, 
        user=user,
        current_user=current_user,
        photos=photos,
        get_current_user=get_current_user
    )

@bp.route('/<int:playdate_id>/photos/<int:photo_id>/delete', methods=['POST'])
def delete_photo(playdate_id, photo_id):
    """
    Delete a photo from a playdate gallery.
    Only the photo uploader or the playdate host can delete photos.
    """
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    photo = PlaydatePhoto.query.get_or_404(photo_id)
    
    # Security check: only the photo uploader or the playdate host can delete
    if photo.user_id != user.id and playdate.host_id != user.id:
        flash('You do not have permission to delete this photo.', 'error')
        return redirect(url_for('playdates.playdate_photos', playdate_id=playdate_id))
    
    # Get the filename to remove the file from disk
    filename = photo.filename
    
    try:
        # Delete the file from the server
        file_path = os.path.join('app/static/playdate_photos', filename)
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete the database record
        db.session.delete(photo)
        db.session.commit()
        
        flash('Photo deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting photo: {str(e)}', 'error')
    
    return redirect(url_for('playdates.playdate_photos', playdate_id=playdate_id))

@bp.route('/playdate/<int:playdate_id>/group-chat')
def playdate_group_chat(playdate_id):
    """
    View the group chat for a playdate
    
    Args:
        playdate_id: ID of the playdate
    
    Returns:
        Rendered template for the playdate group chat
    """
    # Check if user is logged in
    if 'username' not in session:
        flash('Please log in to view the playdate group chat.', 'error')
        return redirect(url_for('auth.login'))
    
    # Get the playdate
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Get all participants (pets and their owners)
    participants = []
    for pet in playdate.pets:
        if pet.owner != playdate.host and pet.owner not in [p.user for p in participants]:
            participants.append({"user": pet.owner, "pet": pet})
    
    # Get the chat history (most recent 50 messages)
    chat_history = PlaydateMessage.query.filter_by(playdate_id=playdate_id) \
        .order_by(PlaydateMessage.timestamp.asc()) \
        .limit(50).all()
    
    return render_template('playdate_group_chat.html', 
                          playdate=playdate, 
                          participants=participants,
                          chat_history=chat_history)

@bp.route('/<int:playdate_id>/edit', methods=['GET', 'POST'])
def edit_playdate(playdate_id):
    """
    Edit a playdate. Only the host can edit a playdate.
    """
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if user is the host
    if playdate.host_id != user.id:
        flash('Only the host can edit a playdate.', 'error')
        return redirect(url_for('playdates.view_playdate', playdate_id=playdate_id))
    
    # Get all pets belonging to the user
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    
    # Get currently selected pets for this playdate
    selected_pet_ids = [pet.id for pet in playdate.pets if pet.owner_id == user.id]
    
    # Format the date for the datetime-local input
    formatted_date = playdate.date.strftime('%Y-%m-%dT%H:%M')
    
    if request.method == 'POST':
        try:
            # Update playdate details
            description = request.form.get('description', '')
            location = request.form['location']
            date_str = request.form['date']
            
            # Parse the datetime
            date_time = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
            
            # Update the playdate
            playdate.description = description
            playdate.location = location
            playdate.date = date_time
            
            # Geocode the updated location
            lat, lng = geocode_address(location)
            if lat and lng:
                playdate.latitude = lat
                playdate.longitude = lng
            
            # Handle pet selection changes
            # First, remove all pets owned by this user
            for pet in list(playdate.pets):
                if pet.owner_id == user.id:
                    playdate.pets.remove(pet)
            
            # Then add back the selected ones
            selected_pets = request.form.getlist('selected_pets')
            for pet_id in selected_pets:
                pet = Pet.query.get(pet_id)
                if pet and pet.owner_id == user.id:
                    playdate.pets.append(pet)
            
            db.session.commit()
            flash('Playdate updated successfully!', 'success')
            return redirect(url_for('playdates.view_playdate', playdate_id=playdate_id))
        
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating playdate: {str(e)}', 'error')
            return render_template(
                'edit_playdate.html',
                playdate=playdate,
                user_pets=user_pets,
                selected_pet_ids=selected_pet_ids,
                formatted_date=formatted_date
            )
    
    return render_template(
        'edit_playdate.html',
        playdate=playdate,
        user_pets=user_pets,
        selected_pet_ids=selected_pet_ids,
        formatted_date=formatted_date
    )

@bp.route('/<int:playdate_id>/delete', methods=['POST'])
def delete_playdate(playdate_id):
    """
    Delete a playdate. Only the host can delete a playdate.
    """
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if user is the host
    if playdate.host_id != user.id:
        flash('Only the host can delete a playdate.', 'error')
        return redirect(url_for('playdates.view_playdate', playdate_id=playdate_id))
    
    try:
        # Delete related photos if any
        photos = PlaydatePhoto.query.filter_by(playdate_id=playdate_id).all()
        for photo in photos:
            # Delete the file from the server if it exists
            photo_path = os.path.join('app/static/playdate_photos', photo.filename)
            if os.path.exists(photo_path):
                os.remove(photo_path)
            db.session.delete(photo)
        
        # Delete related messages if any
        messages = PlaydateMessage.query.filter_by(playdate_id=playdate_id).all()
        for message in messages:
            db.session.delete(message)
        
        # Delete the playdate
        db.session.delete(playdate)
        db.session.commit()
        
        flash('Playdate deleted successfully.', 'success')
        return redirect(url_for('playdates.playdates'))
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting playdate: {str(e)}', 'error')
        return redirect(url_for('playdates.view_playdate', playdate_id=playdate_id)) 