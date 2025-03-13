from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, abort, current_app, make_response
from app import db
from app.models.user import User
from app.models.pet import Pet
from app.models.gallery_photo import GalleryPhoto
from app.models.photo_like import PhotoLike
from app.models.photo_comment import PhotoComment
from app.models.photo_report import PhotoReport
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from sqlalchemy import desc, or_
from functools import wraps
import uuid
from PIL import Image
import io
import re
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SelectField, FileField
from wtforms.validators import DataRequired, Length, Optional
from app.utils.helpers import is_mobile_device

bp = Blueprint('gallery', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            flash('Please log in to access this page', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Helper function to get the current user from session"""
    if 'username' in session:
        return User.query.filter_by(username=session['username']).first()
    return None

class PhotoUploadForm(FlaskForm):
    photo = FileField('Photo', validators=[DataRequired()])
    title = StringField('Title', validators=[Length(max=255)])
    description = TextAreaField('Description', validators=[Optional(), Length(max=1000)])
    pet_id = SelectField('Tag Pet', validators=[Optional()], coerce=int)
    is_public = BooleanField('Public', default=True)

def check_file_type(filename):
    """Check if file is a valid image file by extension"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def check_file_size(file_path, max_size_mb=5):
    """Check if file is within the size limit"""
    file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB
    return file_size <= max_size_mb

def moderate_content(title, description):
    """
    Basic content moderation to check for inappropriate content
    Returns a tuple of (is_appropriate, reason)
    """
    # Define patterns for inappropriate content
    patterns = [
        r'\b(explicit|nude|sex|porn|xxx)\b',
        r'\b(offensive|racist|slur)\b',
        r'\b(gambling|casino|bet)\b',
        r'\b(spam|advertise|buy now|cheap)\b'
    ]
    
    # Combine the title and description for checking
    content = f"{title} {description}".lower()
    
    # Check against patterns
    for pattern in patterns:
        if re.search(pattern, content):
            return False, f"Content contains inappropriate terms matching pattern: {pattern}"
    
    return True, "Content is appropriate"

@bp.route('/gallery')
def index():
    """Main gallery view showing public and user's photos"""
    user = get_current_user()
    
    if not user:
        flash('Please log in to view the gallery', 'error')
        return redirect(url_for('auth.login'))
    
    # Force a completely fresh session to ensure we get the latest data
    db.session.close()
    db.session.expire_all()
    
    # Add diagnostic logging
    current_app.logger.info(f"Gallery index: User={user.username}, ID={user.id}")
    
    # Fetch all photos visible to this user - with eager loading of relationships
    personal_photos = GalleryPhoto.query.options(
        db.joinedload(GalleryPhoto.uploader),
        db.joinedload(GalleryPhoto.pet)
    ).filter_by(user_id=user.id).order_by(GalleryPhoto.created_at.desc()).all()
    
    # Log personal photos
    current_app.logger.info(f"Personal photos found: {len(personal_photos)}")
    
    # Fetch public photos - these should be visible to all users
    public_photos = GalleryPhoto.query.options(
        db.joinedload(GalleryPhoto.uploader),
        db.joinedload(GalleryPhoto.pet)
    ).filter(
        GalleryPhoto.is_public == True,
        GalleryPhoto.moderation_status == 'approved'
    ).order_by(GalleryPhoto.created_at.desc()).all()
    
    # Log public photos
    current_app.logger.info(f"Public photos found: {len(public_photos)}")
    
    # Select photos based on the filter parameter
    filter_param = request.args.get('filter', 'personal')
    if filter_param == 'public':
        photos = public_photos
    else:  # Default to personal
        photos = personal_photos
    
    # Determine active tab
    active_tab = 'my' if filter_param == 'personal' else filter_param
    if active_tab not in ['my', 'public']:
        active_tab = 'my'  # Default to 'my' tab
    
    # Get counts
    like_counts = {}
    comment_counts = {}
    for photo in photos:
        like_counts[photo.id] = PhotoLike.query.filter_by(photo_id=photo.id).count()
        comment_counts[photo.id] = PhotoComment.query.filter_by(photo_id=photo.id).count()
    
    # Get user's pets for filtering
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    
    # Check if mobile mode - ONLY if explicitly requested via query parameter
    is_mobile = False
    
    # Use mobile version if mobile=true is in the query parameter
    if request.args.get('mobile') == 'true':
        is_mobile = True
    else:
        # Desktop is default
        is_mobile = False
    
    # Log which template will be used - use an existing template file
    template = 'mobile_enhanced_gallery.html' if is_mobile else 'enhanced_gallery.html'
    current_app.logger.info(f"Gallery view - Template: {template}, mobile flag: {is_mobile}")
    
    # Set a response object so we can add a cookie
    response = make_response(render_template(
        template,
        user=user,
        photos=photos,
        personal_photos=personal_photos,
        public_photos=public_photos,
        like_counts=like_counts,
        comment_counts=comment_counts,
        user_pets=user_pets,
        active_tab=active_tab
    ))
    
    # Update cookie to remember the preference
    if request.args.get('mobile') == 'true':
        response.set_cookie('preferMobileVersion', 'true', max_age=30*24*60*60)  # 30 days
    elif request.args.get('mobile') == 'false':
        response.set_cookie('preferMobileVersion', 'false', max_age=30*24*60*60)  # 30 days
        
    return response

@bp.route('/mobile-gallery')
def mobile_gallery():
    """Mobile-optimized gallery view with full functionality"""
    user = get_current_user()
    
    if not user:
        flash('Please log in to view the gallery', 'error')
        return redirect(url_for('auth.login'))
    
    # Force a completely fresh session to ensure we get the latest data
    db.session.close()
    db.session.expire_all()
    
    # Add diagnostic logging
    current_app.logger.info(f"Mobile Gallery: User={user.username}, ID={user.id}")
    
    # Fetch all photos visible to this user - with eager loading of relationships
    personal_photos = GalleryPhoto.query.options(
        db.joinedload(GalleryPhoto.uploader),
        db.joinedload(GalleryPhoto.pet)
    ).filter_by(user_id=user.id).order_by(GalleryPhoto.created_at.desc()).all()
    
    # Fetch public photos - these should be visible to all users
    public_photos = GalleryPhoto.query.options(
        db.joinedload(GalleryPhoto.uploader),
        db.joinedload(GalleryPhoto.pet)
    ).filter(
        GalleryPhoto.is_public == True,
        GalleryPhoto.moderation_status == 'approved'
    ).order_by(GalleryPhoto.created_at.desc()).all()
    
    # Fetch featured photos for admins
    featured_photos = []
    if user.is_admin:
        featured_photos = GalleryPhoto.query.options(
            db.joinedload(GalleryPhoto.uploader),
            db.joinedload(GalleryPhoto.pet)
        ).filter(
            GalleryPhoto.is_public == True,
            GalleryPhoto.moderation_status == 'approved',
            GalleryPhoto.featured == True
        ).order_by(GalleryPhoto.created_at.desc()).all()
    
    # Select photos based on the filter parameter
    filter_param = request.args.get('filter', 'personal')
    if filter_param == 'public':
        photos = public_photos
    elif filter_param == 'featured' and user.is_admin:
        photos = featured_photos
    else:  # Default to personal
        photos = personal_photos
    
    # Determine active tab
    active_tab = 'my' if filter_param == 'personal' else filter_param
    if active_tab not in ['my', 'public', 'featured']:
        active_tab = 'my'  # Default to 'my' tab
    
    # Get counts
    like_counts = {}
    comment_counts = {}
    for photo in photos:
        like_counts[photo.id] = PhotoLike.query.filter_by(photo_id=photo.id).count()
        comment_counts[photo.id] = PhotoComment.query.filter_by(photo_id=photo.id).count()
    
    # Get user's pets for filtering
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    
    # Get pet_id filter if it exists
    pet_id = request.args.get('pet_id', '0')
    
    # Get sort_by parameter
    sort_by = request.args.get('sort_by', 'newest')
    
    current_app.logger.info(f"Mobile Gallery view - Template: mobile_enhanced_gallery.html")
    
    # Set a response object
    response = make_response(render_template(
        'mobile_enhanced_gallery.html',
        user=user,
        photos=photos,
        personal_photos=personal_photos,
        public_photos=public_photos,
        featured_photos=featured_photos if user.is_admin else [],
        like_counts=like_counts,
        comment_counts=comment_counts,
        user_pets=user_pets,
        active_tab=active_tab,
        pet_id=pet_id,
        sort_by=sort_by
    ))
    
    return response

@bp.route('/gallery/upload', methods=['GET', 'POST'])
@login_required
def upload_photo():
    """Upload a new photo to the gallery"""
    user = get_current_user()
    
    # Create form and populate pet choices
    form = PhotoUploadForm()
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    form.pet_id.choices = [(0, 'None')] + [(pet.id, pet.name) for pet in user_pets]
    
    if form.validate_on_submit():
        try:
            # Get the uploaded file
            file = form.photo.data
            if file and file.filename:
                # Generate secure filename with timestamp to prevent collisions
                filename = secure_filename(file.filename)
                
                # Validate file type
                if not check_file_type(filename):
                    flash('Invalid file type. Allowed types: PNG, JPG, JPEG, GIF.', 'error')
                    # Check if mobile using the shared function
                    is_mobile = is_mobile_device(request)
                    template = 'mobile_upload_gallery_photo.html' if is_mobile else 'upload_gallery_photo.html'
                    return render_template(template, form=form, user=user, pets=user_pets)
                
                # Add timestamp and user ID to filename to prevent collisions
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                filename = f"user_{user.id}_{timestamp}_{filename}"
                
                # SIMPLIFIED path construction - direct path relative to app root
                file_path = os.path.join('static', 'pet_images', 'gallery_photos', filename)
                absolute_path = os.path.abspath(file_path)
                
                # Log the file path for debugging
                current_app.logger.info(f"UPLOAD DIAGNOSTIC - File path: {file_path}")
                current_app.logger.info(f"UPLOAD DIAGNOSTIC - Absolute path: {absolute_path}")
                
                # Ensure directory exists
                gallery_dir = os.path.dirname(file_path)
                if not os.path.exists(gallery_dir):
                    current_app.logger.info(f"Creating directory: {gallery_dir}")
                    os.makedirs(gallery_dir, exist_ok=True)
                
                current_app.logger.info(f"UPLOAD DIAGNOSTIC - Directory exists: {os.path.exists(gallery_dir)}")
                
                # Save the file
                file.save(file_path)
                
                # Verify file was saved successfully - critical check
                if not os.path.isfile(file_path):
                    raise Exception(f"File was not saved successfully at {file_path}")
                
                # Verify file was saved
                current_app.logger.info(f"UPLOAD DIAGNOSTIC - File saved successfully: {os.path.isfile(file_path)}")
                current_app.logger.info(f"UPLOAD DIAGNOSTIC - File size: {os.path.getsize(file_path) if os.path.isfile(file_path) else 'N/A'}")
                
                # Check file size after saving
                if not check_file_size(file_path):
                    # Remove the file if it's too large
                    os.remove(file_path)
                    flash('File size exceeds the 5MB limit.', 'error')
                    # Check if mobile using the shared function
                    is_mobile = is_mobile_device(request)
                    template = 'mobile_upload_gallery_photo.html' if is_mobile else 'upload_gallery_photo.html'
                    return render_template(template, form=form, user=user, pets=user_pets)
                
                # Check content moderation for title and description
                is_appropriate, reason = moderate_content(form.title.data or '', form.description.data or '')
                moderation_status = 'approved' if is_appropriate else 'pending'
                
                # Create new gallery photo
                pet_id = form.pet_id.data if form.pet_id.data != 0 else None
                new_photo = GalleryPhoto(
                    user_id=user.id,
                    pet_id=pet_id,
                    filename=filename,
                    title=form.title.data,
                    description=form.description.data,
                    is_public=form.is_public.data,
                    moderation_status=moderation_status,
                    share_uuid=str(uuid.uuid4())  # Ensure share_uuid is set
                )
                
                # Explicitly flush to ensure the record is created with an ID
                db.session.add(new_photo)
                db.session.commit()
                
                # Force a reload of the user's photos to ensure they appear in the gallery
                db.session.refresh(new_photo)
                
                # Double-check file existence one more time after committing to the database
                if not os.path.isfile(file_path):
                    # Critical error - file disappeared after database commit
                    current_app.logger.error(f"CRITICAL: File disappeared after database commit. Rolling back transaction.")
                    db.session.delete(new_photo)
                    db.session.commit()
                    raise Exception("File was saved but then disappeared. Please try again.")
                
                # Add diagnostic logging
                current_app.logger.info(f"Photo uploaded: id={new_photo.id}, user_id={user.id}, filename={filename}, moderation_status={moderation_status}")
                
                # Check if the photo is now in the database
                verification = GalleryPhoto.query.get(new_photo.id)
                if verification:
                    current_app.logger.info(f"Verified photo in DB: id={verification.id}, filename={verification.filename}")
                else:
                    current_app.logger.error(f"CRITICAL: Photo not found in DB after upload: id={new_photo.id}")
                
                if moderation_status == 'pending':
                    flash('Your photo has been uploaded and is pending review.', 'warning')
                else:
                    flash('Your photo has been uploaded successfully!', 'success')
                
                # Redirect with a timestamp to prevent caching
                timestamp = int(datetime.now().timestamp())
                return redirect(url_for('gallery.index', t=timestamp))
                
        except Exception as e:
            # Roll back any database changes if there was an error
            db.session.rollback()
            
            # Log the error
            current_app.logger.error(f"Error during photo upload: {str(e)}")
            
            # Provide a user-friendly error message
            flash(f'There was an error uploading your photo: {str(e)}', 'error')
    
    # Enhanced mobile detection with logging for debugging
    is_mobile = is_mobile_device(request)
    
    # Additional debug info
    user_agent = request.headers.get('User-Agent', '')
    
    # Force mobile template for development/testing if needed
    debug_mobile = request.args.get('force_mobile') == 'true'
    if debug_mobile:
        is_mobile = True
    
    # Use mobile template for mobile devices, regular template for desktop
    template = 'mobile_upload_gallery_photo.html' if is_mobile else 'upload_gallery_photo.html'
    
    # Log detection result for debugging
    current_app.logger.info(f"Mobile detection: {is_mobile}, UA: {user_agent[:50]}...")
    
    return render_template(template, form=form, user=user, pets=user_pets, user_agent=user_agent, is_mobile=is_mobile)

@bp.route('/gallery/mobile-upload', methods=['GET', 'POST'])
@login_required
def mobile_upload_photo():
    """Upload a new photo to the gallery (mobile version)"""
    user = get_current_user()
    
    # Create form and populate pet choices
    form = PhotoUploadForm()
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    form.pet_id.choices = [(0, 'None')] + [(pet.id, pet.name) for pet in user_pets]
    
    if form.validate_on_submit():
        try:
            # Process form submission similar to upload_photo function
            file = form.photo.data
            if file and file.filename:
                # Generate secure filename with timestamp to prevent collisions
                filename = secure_filename(file.filename)
                
                # Validate file type
                if not check_file_type(filename):
                    flash('Invalid file type. Allowed types: PNG, JPG, JPEG, GIF.', 'error')
                    return render_template('mobile_upload_gallery_photo.html', form=form, user=user, pets=user_pets)
                
                # Add timestamp and user ID to filename to prevent collisions
                timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                filename = f"user_{user.id}_{timestamp}_{filename}"
                
                # SIMPLIFIED path construction - direct path relative to app root
                file_path = os.path.join('static', 'pet_images', 'gallery_photos', filename)
                absolute_path = os.path.abspath(file_path)
                
                # Log file path for debugging
                current_app.logger.info(f"MOBILE UPLOAD - File path: {file_path}")
                current_app.logger.info(f"MOBILE UPLOAD - Absolute path: {absolute_path}")
                
                # Ensure directory exists
                gallery_dir = os.path.dirname(file_path)
                if not os.path.exists(gallery_dir):
                    current_app.logger.info(f"Creating directory: {gallery_dir}")
                    os.makedirs(gallery_dir, exist_ok=True)
                
                # Save the file
                file.save(file_path)
                
                # Verify file was saved successfully - critical check
                if not os.path.isfile(file_path):
                    raise Exception(f"File was not saved successfully at {file_path}")
                
                # Log file saving results
                current_app.logger.info(f"MOBILE UPLOAD - File saved: {os.path.isfile(file_path)}")
                current_app.logger.info(f"MOBILE UPLOAD - File size: {os.path.getsize(file_path) if os.path.isfile(file_path) else 'N/A'}")
                
                # Check file size after saving
                if not check_file_size(file_path):
                    # Remove the file if it's too large
                    os.remove(file_path)
                    flash('File size exceeds the 5MB limit.', 'error')
                    return render_template('mobile_upload_gallery_photo.html', form=form, user=user, pets=user_pets)
                
                # Use the same moderation and database logic as the regular upload_photo function
                is_appropriate, reason = moderate_content(form.title.data or '', form.description.data or '')
                moderation_status = 'approved' if is_appropriate else 'pending'
                
                # Create new gallery photo
                pet_id = form.pet_id.data if form.pet_id.data != 0 else None
                new_photo = GalleryPhoto(
                    user_id=user.id,
                    pet_id=pet_id,
                    filename=filename,
                    title=form.title.data,
                    description=form.description.data,
                    is_public=form.is_public.data,
                    moderation_status=moderation_status,
                    share_uuid=str(uuid.uuid4())  # Ensure share_uuid is set
                )
                
                # Add to database and commit in a single transaction
                db.session.add(new_photo)
                db.session.commit()
                
                # Force a reload of the user's photos to ensure they appear in the gallery
                db.session.refresh(new_photo)
                
                # Double-check file existence one more time after committing to the database
                if not os.path.isfile(file_path):
                    # Critical error - file disappeared after database commit
                    current_app.logger.error(f"CRITICAL: File disappeared after database commit. Rolling back transaction.")
                    db.session.delete(new_photo)
                    db.session.commit()
                    raise Exception("File was saved but then disappeared. Please try again.")
                
                # Add diagnostic logging
                current_app.logger.info(f"Mobile photo uploaded: id={new_photo.id}, user_id={user.id}, filename={filename}")
                
                # Check if the photo is now in the database
                verification = GalleryPhoto.query.get(new_photo.id)
                if verification:
                    current_app.logger.info(f"Verified mobile photo in DB: id={verification.id}, filename={verification.filename}")
                else:
                    current_app.logger.error(f"CRITICAL: Mobile photo not found in DB after upload: id={new_photo.id}")
                
                if moderation_status == 'pending':
                    flash('Your photo has been uploaded and is pending review.', 'warning')
                else:
                    flash('Your photo has been uploaded successfully!', 'success')
                
                # Redirect with a timestamp to prevent caching
                timestamp = int(datetime.now().timestamp())
                return redirect(url_for('gallery.mobile_gallery', t=timestamp))
        
        except Exception as e:
            # Roll back any database changes if there was an error
            db.session.rollback()
            
            # Log the error
            current_app.logger.error(f"Error during mobile photo upload: {str(e)}")
            
            # Provide a user-friendly error message
            flash(f'There was an error uploading your photo: {str(e)}', 'error')
    
    # Get user agent for debugging
    user_agent = request.headers.get('User-Agent', '')
    
    # Always use mobile template for this route, regardless of device
    is_mobile = True
    return render_template('mobile_upload_gallery_photo.html', form=form, user=user, pets=user_pets, 
                          user_agent=user_agent, is_mobile=is_mobile)

@bp.route('/gallery/photo/<int:photo_id>')
def view_photo(photo_id):
    """View a single photo with comments and likes"""
    user = get_current_user()
    if not user:
        flash('Please log in to view photos', 'error')
        return redirect(url_for('auth.login'))
    
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Check if user has permission to view this photo
    if not photo.is_public and photo.user_id != user.id:
        flash('You do not have permission to view this photo', 'error')
        return redirect(url_for('gallery.index'))
    
    # Increment view count
    photo.increment_view_count()
    
    # Get comments
    comments = PhotoComment.query.filter_by(photo_id=photo_id).order_by(PhotoComment.created_at.desc()).all()
    
    # Check if user has liked this photo
    user_like = PhotoLike.query.filter_by(user_id=user.id, photo_id=photo_id).first()
    
    # Get like count
    like_count = PhotoLike.query.filter_by(photo_id=photo_id).count()
    
    # Check if mobile
    is_mobile = any(device in request.headers.get('User-Agent', '').lower() 
                   for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    template = 'mobile_view_enhanced_photo.html' if is_mobile else 'view_enhanced_photo.html'
    
    return render_template(
        template,
        photo=photo,
        comments=comments,
        user_like=user_like,
        like_count=like_count,
        user=user
    )

@bp.route('/gallery/photo/<int:photo_id>/like', methods=['POST'])
@login_required
def like_photo(photo_id):
    """Like or unlike a photo"""
    user = get_current_user()
    
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Check if the user already liked this photo
    existing_like = PhotoLike.query.filter_by(user_id=user.id, photo_id=photo_id).first()
    
    if existing_like:
        # Unlike
        db.session.delete(existing_like)
        action = 'unliked'
    else:
        # Like
        like = PhotoLike(user_id=user.id, photo_id=photo_id)
        db.session.add(like)
        action = 'liked'
    
    db.session.commit()
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        like_count = PhotoLike.query.filter_by(photo_id=photo_id).count()
        return jsonify({
            'success': True,
            'action': action,
            'like_count': like_count
        })
    
    flash(f'Photo {action}!', 'success')
    return redirect(url_for('gallery.view_photo', photo_id=photo_id))

@bp.route('/gallery/photo/<int:photo_id>/comment', methods=['POST'])
@login_required
def add_comment(photo_id):
    """Add a comment to a photo"""
    user = get_current_user()
    
    photo = GalleryPhoto.query.get_or_404(photo_id)
    comment_text = request.form.get('comment', '').strip()
    
    if not comment_text:
        flash('Comment cannot be empty', 'error')
        return redirect(url_for('gallery.view_photo', photo_id=photo_id))
    
    # Create new comment
    comment = PhotoComment(
        user_id=user.id,
        photo_id=photo_id,
        comment=comment_text
    )
    
    db.session.add(comment)
    db.session.commit()
    
    flash('Comment added!', 'success')
    return redirect(url_for('gallery.view_photo', photo_id=photo_id))

@bp.route('/gallery/photo/<int:photo_id>/report', methods=['GET', 'POST'])
@login_required
def report_photo(photo_id):
    """Report a photo for inappropriate content"""
    user = get_current_user()
    
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    if request.method == 'POST':
        reason = request.form.get('reason')
        details = request.form.get('details', '')
        
        if not reason:
            flash('Please select a reason for the report', 'error')
            return redirect(url_for('gallery.report_photo', photo_id=photo_id))
        
        # Check if already reported
        existing_report = PhotoReport.query.filter_by(user_id=user.id, photo_id=photo_id).first()
        if existing_report:
            flash('You have already reported this photo', 'warning')
            return redirect(url_for('gallery.view_photo', photo_id=photo_id))
        
        # Create report
        report = PhotoReport(
            user_id=user.id,
            photo_id=photo_id,
            reason=reason,
            details=details
        )
        
        db.session.add(report)
        db.session.commit()
        
        flash('Thank you for your report. Our team will review it.', 'success')
        return redirect(url_for('gallery.view_photo', photo_id=photo_id))
    
    # Check if mobile
    is_mobile = any(device in request.headers.get('User-Agent', '').lower() 
                   for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    template = 'mobile_report_photo.html' if is_mobile else 'report_photo.html'
    
    return render_template(template, photo=photo, user=user)

@bp.route('/gallery/photo/<int:photo_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_photo(photo_id):
    """Edit photo metadata"""
    user = get_current_user()
    
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Check if user owns the photo
    if photo.user_id != user.id:
        flash('You can only edit your own photos', 'error')
        return redirect(url_for('gallery.index'))
    
    # Get user's pets for the form
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    
    if request.method == 'POST':
        try:
            photo.title = request.form.get('title')
            photo.description = request.form.get('description')
            photo.is_public = 'is_public' in request.form
            
            pet_id = request.form.get('pet_id')
            photo.pet_id = int(pet_id) if pet_id and pet_id != '0' else None
            
            db.session.commit()
            flash('Photo updated successfully!', 'success')
            return redirect(url_for('gallery.view_photo', photo_id=photo.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating photo: {str(e)}', 'error')
    
    # Check if mobile
    is_mobile = any(device in request.headers.get('User-Agent', '').lower() 
                   for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    template = 'mobile_edit_gallery_photo.html' if is_mobile else 'edit_gallery_photo.html'
    
    return render_template(
        template,
        photo=photo,
        pets=user_pets,
        user=user
    )

@bp.route('/gallery/photo/<int:photo_id>/delete', methods=['POST'])
@login_required
def delete_photo(photo_id):
    """Delete a photo"""
    user = get_current_user()
    
    photo = GalleryPhoto.query.get_or_404(photo_id)
    
    # Check if user owns the photo or is admin
    if photo.user_id != user.id and not user.is_admin:
        flash('You can only delete your own photos', 'error')
        return redirect(url_for('gallery.index'))
    
    try:
        # Delete physical file (only in static directory)
        file_path = os.path.join(os.path.dirname(os.path.dirname(current_app.config['UPLOAD_FOLDER'])), 
                                'static', 'pet_images', 'gallery_photos', photo.filename)
        
        # Attempt to remove the file
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Delete from database (cascade will handle related records)
        db.session.delete(photo)
        db.session.commit()
        
        flash('Photo deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting photo: {str(e)}', 'error')
    
    return redirect(url_for('gallery.index'))

@bp.route('/gallery/share/<string:share_uuid>')
def shared_photo(share_uuid):
    """View a shared photo via unique link - no login required"""
    photo = GalleryPhoto.query.filter_by(share_uuid=share_uuid).first_or_404()
    
    # Increment view count
    photo.increment_view_count()
    
    # Get uploader info
    uploader = User.query.get(photo.user_id)
    
    # Get like count
    like_count = PhotoLike.query.filter_by(photo_id=photo.id).count()
    
    # Check if mobile
    is_mobile = any(device in request.headers.get('User-Agent', '').lower() 
                   for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    template = 'mobile_view_enhanced_photo.html' if is_mobile else 'view_enhanced_photo.html'
    
    return render_template(
        template,
        photo=photo,
        uploader=uploader,
        like_count=like_count,
        user=None
    )

@bp.route('/gallery/filter', methods=['GET'])
@login_required
def filter_gallery():
    """Filter gallery photos"""
    user = get_current_user()
    
    filter_type = request.args.get('filter', 'personal')
    pet_id = request.args.get('pet_id')
    sort_by = request.args.get('sort_by', 'newest')
    
    # Base query for user's personal photos with eager loading
    personal_query = GalleryPhoto.query.options(
        db.joinedload(GalleryPhoto.uploader),
        db.joinedload(GalleryPhoto.pet)
    ).filter_by(user_id=user.id)
    
    # Base query for public photos with eager loading
    public_query = GalleryPhoto.query.options(
        db.joinedload(GalleryPhoto.uploader),
        db.joinedload(GalleryPhoto.pet)
    ).filter(
        GalleryPhoto.is_public == True,
        GalleryPhoto.moderation_status == 'approved'
    )
    
    # Base query for featured photos with eager loading (for admins)
    featured_query = None
    if user.is_admin:
        featured_query = GalleryPhoto.query.options(
            db.joinedload(GalleryPhoto.uploader),
            db.joinedload(GalleryPhoto.pet)
        ).filter(
            GalleryPhoto.is_public == True,
            GalleryPhoto.moderation_status == 'approved',
            GalleryPhoto.featured == True
        )
    
    # Apply pet filter if specified
    if pet_id and pet_id.isdigit() and int(pet_id) > 0:
        pet_id = int(pet_id)
        personal_query = personal_query.filter_by(pet_id=pet_id)
        public_query = public_query.filter_by(pet_id=pet_id)
        if featured_query:
            featured_query = featured_query.filter_by(pet_id=pet_id)
    
    # Get photos based on filter type
    if filter_type == 'public':
        photos = public_query.all()
    elif filter_type == 'featured' and user.is_admin and featured_query:
        photos = featured_query.all()
    else:  # Default to personal
        photos = personal_query.all()
    
    # Apply sorting
    if sort_by == 'oldest':
        photos.sort(key=lambda x: x.created_at)
    elif sort_by == 'most_liked':
        # This requires a more complex query with join, so we'll handle it in Python
        # Get like counts for each photo
        like_counts = {photo.id: PhotoLike.query.filter_by(photo_id=photo.id).count() for photo in photos}
        photos.sort(key=lambda x: like_counts.get(x.id, 0), reverse=True)
    elif sort_by == 'most_viewed':
        photos.sort(key=lambda x: x.view_count, reverse=True)
    else:  # 'newest'
        photos.sort(key=lambda x: x.created_at, reverse=True)
    
    # Get counts for rendering
    like_counts = {photo.id: PhotoLike.query.filter_by(photo_id=photo.id).count() for photo in photos}
    comment_counts = {photo.id: PhotoComment.query.filter_by(photo_id=photo.id).count() for photo in photos}
    
    # Get user's pets for filtering
    user_pets = Pet.query.filter_by(owner_id=user.id).all()
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return HTML fragment for the photos
        html = render_template(
            'photo_grid_fragment.html',
            photos=photos,
            like_counts=like_counts,
            comment_counts=comment_counts,
            user=user
        )
        return jsonify({'html': html})
    
    # Determine if mobile view was explicitly requested
    is_mobile = request.args.get('mobile') == 'true'
    
    # If not explicit, check user agent for mobile device
    if not is_mobile:
        is_mobile = any(device in request.headers.get('User-Agent', '').lower() 
                      for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    # Log template selection
    template = 'mobile_enhanced_gallery.html' if is_mobile else 'enhanced_gallery.html'
    current_app.logger.info(f"Filter Gallery - Template: {template}, mobile flag: {is_mobile}")
    
    # Get all photo collections for the template
    personal_photos = personal_query.all()
    public_photos = public_query.all()
    featured_photos = featured_query.all() if featured_query else []
    
    # Determine active tab
    active_tab = 'my' if filter_type == 'personal' else filter_type
    
    return render_template(
        template,
        user=user,
        photos=photos,
        personal_photos=personal_photos,
        public_photos=public_photos,
        featured_photos=featured_photos,
        like_counts=like_counts,
        comment_counts=comment_counts,
        filter_type=filter_type,
        pet_id=pet_id,
        sort_by=sort_by,
        user_pets=user_pets,
        active_tab=active_tab
    ) 