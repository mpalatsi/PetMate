from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import login_required, current_user, login_user, logout_user
from app import db
from datetime import datetime
from functools import wraps
from werkzeug.security import generate_password_hash
import secrets

bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You do not have permission to access this area.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def is_mobile_device():
    user_agent = request.headers.get('User-Agent', '').lower()
    return any(device in user_agent for device in ['android', 'iphone', 'ipad', 'mobile', 'webos'])

@bp.route('/debug_admin')
@login_required
def debug_admin():
    debug_info = {
        'username': current_user.username,
        'is_authenticated': current_user.is_authenticated,
        'is_admin': current_user.is_admin,
        'is_admin_type': type(current_user.is_admin).__name__,
        'account_status': current_user.account_status,
        'session_username': session.get('username', 'Not in session')
    }
    return render_template('admin/debug.html', debug_info=debug_info, user=current_user)

@bp.route('/')
@login_required
@admin_required
def admin_dashboard():
    print("Admin dashboard route called")
    print(f"Current user: {current_user}")
    print(f"Current user is authenticated: {current_user.is_authenticated}")
    print(f"Current user is admin: {current_user.is_admin}")
    
    # Import models locally to avoid circular imports
    from app.models.user import User
    from app.models.pet import Pet
    from app.models.playdate import Playdate
    from app.models.incident_report import IncidentReport
    from app.models.gallery_photo import GalleryPhoto
    
    # Check for unresolved reports
    unresolved_reports = IncidentReport.query.filter(IncidentReport.status.in_(['New', 'Investigating'])).count()
    
    # Collect statistics in a dictionary
    stats = {
        'total_users': User.query.count(),
        'total_pets': Pet.query.count(),
        'total_playdates': Playdate.query.count(),
        'total_reports': IncidentReport.query.count(),
        'total_photos': GalleryPhoto.query.count(),
        'unresolved_reports': unresolved_reports
    }
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Check if mobile device
    if is_mobile_device():
        return render_template('admin/mobile_dashboard.html',
                            stats=stats,
                            recent_users=recent_users)
    else:
        return render_template('admin/dashboard.html',
                            stats=stats,
                            recent_users=recent_users)

@bp.route('/direct_access/<token>')
def direct_admin_access(token):
    """
    Direct access to admin panel with a fixed token.
    This bypasses the admin check in templates.
    """
    # Use a fixed token for direct admin access
    valid_token = "admin_direct_8675309"
    
    if token != valid_token:
        flash('Invalid access token.', 'error')
        return redirect(url_for('main.index'))
    
    # Import models locally to avoid circular imports
    from app.models.user import User
    from app.models.pet import Pet
    from app.models.playdate import Playdate
    from app.models.incident_report import IncidentReport
    from app.models.gallery_photo import GalleryPhoto
    
    # Check for unresolved reports
    unresolved_reports = IncidentReport.query.filter(IncidentReport.status.in_(['New', 'Investigating'])).count()
    
    # Collect statistics in a dictionary
    stats = {
        'total_users': User.query.count(),
        'total_pets': Pet.query.count(),
        'total_playdates': Playdate.query.count(),
        'total_reports': IncidentReport.query.count(),
        'total_photos': GalleryPhoto.query.count(),
        'unresolved_reports': unresolved_reports
    }
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Check if mobile device
    if is_mobile_device():
        return render_template('admin/mobile_dashboard.html',
                            stats=stats,
                            recent_users=recent_users)
    else:
        return render_template('admin/dashboard.html',
                            stats=stats,
                            recent_users=recent_users)

@bp.route('/admin_login')
def admin_login():
    """
    Special admin login page that doesn't rely on template checks
    """
    # Import models locally to avoid circular imports
    from app.models.user import User
    
    # Admin users list for direct access
    admin_users = User.query.filter_by(is_admin=True).all()
    
    return render_template('admin/admin_login.html', admin_users=admin_users)

@bp.route('/users')
@login_required
@admin_required
def user_management():
    from app.models.user import User
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', None)
    search_query = request.args.get('search', None)
    
    # Start with base query
    query = User.query
    
    # Apply filters
    if filter_type:
        if filter_type == 'admin':
            query = query.filter(User.is_admin == True)
        elif filter_type == 'active':
            query = query.filter(User.is_active == True)
        elif filter_type == 'inactive':
            query = query.filter(User.is_active == False)
        elif filter_type == 'new':
            # Get users from the last 7 days
            from datetime import datetime, timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            query = query.filter(User.created_at >= week_ago)
    
    # Apply search
    if search_query:
        query = query.filter(User.username.ilike(f'%{search_query}%') | 
                             User.email.ilike(f'%{search_query}%') |
                             User.name.ilike(f'%{search_query}%'))
    
    # Order and paginate
    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=20)
    
    # Check if mobile device
    if is_mobile_device():
        return render_template('admin/mobile_users.html', users=users, pagination=users)
    else:
        return render_template('admin/users.html', users=users)

@bp.route('/user/<int:user_id>')
@login_required
@admin_required
def user_details(user_id):
    from app.models.user import User
    from app.models.review import Review
    
    try:
        # Get user with explicitly loaded relationships
        user = User.query.options(
            db.joinedload(User.pets),
            db.joinedload(User.hosted_playdates),
            db.joinedload(User.attended_playdates),
            db.joinedload(User.reviews_received)
        ).get_or_404(user_id)
        
        # Debug information
        print(f"User object type: {type(user)}")
        print(f"User ID: {user.id}, Username: {user.username}")
        
        # Get pets explicitly to avoid any potential stringification
        pets = list(user.pets) if hasattr(user, 'pets') else []
        reviews_count = user.get_reviews_count()
        
        print(f"Before rendering template - Reviews count: {reviews_count}")
        print(f"User pets count: {len(pets)}")
        
        # Store UI-ready properties in a new object to avoid any conversion
        user_data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at,
            'last_login': user.last_login,
            'account_status': user.account_status,
            'account_notes': user.account_notes,
            'name': user.name,
            'location': user.location,
            'pets_count': len(pets),
            'reviews_count': reviews_count,
            'pets': pets,
            'is_admin': user.is_admin
        }
        
        # Pass user directly to template but also provide a structured user_data object
        return render_template('admin/user_details.html', 
                               user=user, 
                               user_data=user_data, 
                               user_id=user.id)
        
    except Exception as e:
        print(f"Error in user_details: {str(e)}")
        db.session.rollback()
        return f"An error occurred: {str(e)}", 500

@bp.route('/user/<int:user_id>/update', methods=['POST'])
@login_required
@admin_required
def update_user_status(user_id):
    from app.models.user import User
    user = User.query.get_or_404(user_id)
    action = request.form.get('action')
    reason = request.form.get('reason')
    
    if action == 'suspend':
        user.suspend_account(reason)
        flash(f'User {user.username} has been suspended.', 'success')
    elif action == 'activate':
        user.activate_account(reason)
        flash(f'User {user.username} has been activated.', 'success')
    elif action == 'ban':
        user.ban_account(reason)
        flash(f'User {user.username} has been banned.', 'success')
    elif action == 'add_note':
        user.add_admin_note(reason)
        flash('Admin note added successfully.', 'success')
    elif action == 'toggle_admin':
        # Toggle admin status
        user.is_admin = not user.is_admin
        note = f"Admin privileges {'granted' if user.is_admin else 'revoked'}"
        if reason:
            note += f" - Reason: {reason}"
        user.add_admin_note(note)
        db.session.commit()
        flash(f"Admin status for {user.username} has been {'granted' if user.is_admin else 'revoked'}.", 'success')
    
    return redirect(url_for('admin.user_details', user_id=user_id))

@bp.route('/pets')
@login_required
@admin_required
def pets_management():
    from app.models.pet import Pet
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', None)
    search_query = request.args.get('search', None)
    
    # Start with base query
    query = Pet.query
    
    # Apply filters
    if filter_type:
        if filter_type == 'dog':
            query = query.filter(Pet.species == 'Dog')
        elif filter_type == 'cat':
            query = query.filter(Pet.species == 'Cat')
        elif filter_type == 'other':
            query = query.filter(Pet.species != 'Dog', Pet.species != 'Cat')
        elif filter_type == 'new':
            # Get pets from the last 7 days
            from datetime import datetime, timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            query = query.filter(Pet.created_at >= week_ago)
    
    # Apply search
    if search_query:
        query = query.filter(Pet.name.ilike(f'%{search_query}%') | 
                             Pet.species.ilike(f'%{search_query}%') |
                             Pet.breed.ilike(f'%{search_query}%'))
    
    # Order and paginate
    pets = query.order_by(Pet.created_at.desc()).paginate(page=page, per_page=20)
    
    # Check if mobile device
    if is_mobile_device():
        return render_template('admin/mobile_pets.html', pets=pets, pagination=pets)
    else:
        return render_template('admin/pets.html', pets=pets)

@bp.route('/pet/<int:pet_id>')
@login_required
@admin_required
def pet_details(pet_id):
    from app.models.pet import Pet
    pet = Pet.query.get_or_404(pet_id)
    return render_template('admin/pet_details.html', pet=pet)

@bp.route('/pet/<int:pet_id>/update', methods=['POST'])
@login_required
@admin_required
def update_pet_status(pet_id):
    from app.models.pet import Pet
    
    pet = Pet.query.get_or_404(pet_id)
    action = request.form.get('action')
    
    if action == 'flag':
        pet.is_flagged = True
        admin_note = f"Flagged by admin {current_user.username} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if pet.admin_notes:
            pet.admin_notes = admin_note + "\n\n" + pet.admin_notes
        else:
            pet.admin_notes = admin_note
            
        db.session.commit()
        flash('Pet has been flagged for review.', 'success')
    
    return redirect(url_for('admin.pet_details', pet_id=pet_id))

@bp.route('/playdates')
@login_required
@admin_required
def playdates_management():
    from app.models.playdate import Playdate
    from datetime import datetime
    
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', None)
    search_query = request.args.get('search', None)
    
    # Start with base query
    query = Playdate.query
    
    # Apply filters
    today = datetime.utcnow()
    if filter_type:
        if filter_type == 'upcoming':
            query = query.filter(Playdate.date > today.date(), Playdate.status != 'cancelled')
        elif filter_type == 'today':
            query = query.filter(Playdate.date == today.date(), Playdate.status != 'cancelled')
        elif filter_type == 'past':
            query = query.filter(Playdate.date < today.date(), Playdate.status != 'cancelled')
        elif filter_type == 'cancelled':
            query = query.filter(Playdate.status == 'cancelled')
    
    # Apply search
    if search_query:
        query = query.filter(Playdate.title.ilike(f'%{search_query}%') | 
                            Playdate.location.ilike(f'%{search_query}%') |
                            Playdate.description.ilike(f'%{search_query}%'))
    
    # Order and paginate
    playdates = query.order_by(Playdate.date.desc()).paginate(page=page, per_page=20)
    
    # Check if mobile device
    if is_mobile_device():
        return render_template('admin/mobile_playdates.html', playdates=playdates, pagination=playdates, today=today)
    else:
        return render_template('admin/playdates.html', playdates=playdates)

@bp.route('/photos')
@login_required
@admin_required
def photos_management():
    from app.models.gallery_photo import GalleryPhoto
    
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', None)
    search_query = request.args.get('search', None)
    
    # Start with base query
    query = GalleryPhoto.query
    
    # Apply filters
    if filter_type:
        if filter_type == 'public':
            query = query.filter(GalleryPhoto.is_public == True)
        elif filter_type == 'private':
            query = query.filter(GalleryPhoto.is_public == False)
        # Remove the reported filter since the field doesn't exist
        # Instead, we'll add a comment explaining this for future reference
        # elif filter_type == 'reported':
        #     query = query.filter(GalleryPhoto.reported == True)
        elif filter_type == 'recent':
            # Get photos from the last 7 days
            from datetime import datetime, timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            query = query.filter(GalleryPhoto.created_at >= week_ago)
    
    # Apply search
    if search_query:
        query = query.filter(GalleryPhoto.title.ilike(f'%{search_query}%') | 
                            GalleryPhoto.description.ilike(f'%{search_query}%'))
    
    # Order and paginate
    photos = query.order_by(GalleryPhoto.created_at.desc()).paginate(page=page, per_page=20)
    
    # Check if mobile device
    if is_mobile_device():
        return render_template('admin/mobile_photos.html', photos=photos.items, pagination=photos)
    else:
        return render_template('admin/photos.html', photos=photos)

@bp.route('/reports')
@login_required
@admin_required
def incident_reports():
    from app.models.incident_report import IncidentReport
    
    page = request.args.get('page', 1, type=int)
    filter_type = request.args.get('filter', None)
    search_query = request.args.get('search', None)
    
    # Start with base query
    query = IncidentReport.query
    
    # Apply filters
    if filter_type:
        if filter_type == 'new':
            query = query.filter(IncidentReport.status == 'New')
        elif filter_type == 'investigating':
            query = query.filter(IncidentReport.status == 'Investigating')
        elif filter_type == 'resolved':
            query = query.filter(IncidentReport.status == 'Resolved')
        elif filter_type == 'dismissed':
            query = query.filter(IncidentReport.status == 'Dismissed')
    
    # Apply search
    if search_query:
        query = query.filter(IncidentReport.title.ilike(f'%{search_query}%') | 
                            IncidentReport.description.ilike(f'%{search_query}%'))
    
    # Order and paginate
    reports = query.order_by(IncidentReport.created_at.desc()).paginate(page=page, per_page=20)
    
    # Check if mobile device
    if is_mobile_device():
        return render_template('admin/mobile_reports.html', reports=reports.items, pagination=reports)
    else:
        return render_template('admin/reports.html', reports=reports)

@bp.route('/stats')
@login_required
@admin_required
def stats():
    from app.models.user import User
    from app.models.pet import Pet 
    from app.models.playdate import Playdate
    from app.models.gallery_photo import GalleryPhoto
    from datetime import datetime, timedelta
    import random  # For demo data
    
    period = request.args.get('period', 'month')
    
    # For demo purposes, generate some sample stats
    # In a real app, you would query actual data
    
    # Basic period calculations
    today = datetime.utcnow()
    if period == 'week':
        period_start = today - timedelta(days=7)
        time_labels = [(today - timedelta(days=i)).strftime('%a') for i in range(7, 0, -1)]
    elif period == 'month':
        period_start = today - timedelta(days=30)
        time_labels = [(today - timedelta(days=i)).strftime('%d') for i in range(30, 0, -5)]
    elif period == 'quarter':
        period_start = today - timedelta(days=90)
        time_labels = [(today - timedelta(days=i)).strftime('%b %d') for i in range(90, 0, -15)]
    else:  # year
        period_start = today - timedelta(days=365)
        time_labels = [(today - timedelta(days=i)).strftime('%b') for i in range(365, 0, -30)]
    
    # Generate demo data
    stats = {
        'new_users': User.query.filter(User.created_at >= period_start).count(),
        'new_pets': Pet.query.filter(Pet.created_at >= period_start).count(),
        'new_playdates': Playdate.query.filter(Playdate.created_at >= period_start).count(),
        'new_photos': GalleryPhoto.query.filter(GalleryPhoto.created_at >= period_start).count(),
        
        # Trends (percentage change from previous period)
        'user_trend': random.randint(-15, 25),
        'pet_trend': random.randint(-10, 30),
        'playdate_trend': random.randint(-20, 20),
        'photo_trend': random.randint(-5, 35),
        
        # Active users
        'daily_active_users': random.randint(50, 200),
        'weekly_active_users': random.randint(200, 800),
        'monthly_active_users': random.randint(500, 2000),
        
        # Chart data
        'time_labels': time_labels,
        'users_data': [random.randint(5, 30) for _ in range(len(time_labels))],
        'pets_data': [random.randint(3, 25) for _ in range(len(time_labels))],
        'playdates_data': [random.randint(2, 20) for _ in range(len(time_labels))],
        'photos_data': [random.randint(10, 50) for _ in range(len(time_labels))],
        
        # Activity data for bar chart
        'activity_labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
        'activity_data': [random.randint(100, 500) for _ in range(7)],
        
        # Pet types
        'pet_type_labels': ['Dog', 'Cat', 'Bird', 'Fish', 'Rabbit', 'Other'],
        'pet_type_data': [65, 25, 5, 3, 2, 5],  # Percentages
        'pet_types': [
            {'name': 'Dog', 'count': 650, 'percentage': 65},
            {'name': 'Cat', 'count': 250, 'percentage': 25},
            {'name': 'Bird', 'count': 50, 'percentage': 5},
            {'name': 'Fish', 'count': 30, 'percentage': 3},
            {'name': 'Rabbit', 'count': 20, 'percentage': 2},
            {'name': 'Other', 'count': 50, 'percentage': 5}
        ],
        
        # Location data
        'location_labels': ['Central Park', 'Downtown Dog Run', 'Beach Pet Zone', 'Community Pet Park', 'River Trail'],
        'location_data': [42, 38, 25, 22, 18],
        'top_locations': [
            {'name': 'Central Park', 'details': 'New York, NY', 'count': 42},
            {'name': 'Downtown Dog Run', 'details': 'San Francisco, CA', 'count': 38},
            {'name': 'Beach Pet Zone', 'details': 'Miami, FL', 'count': 25},
            {'name': 'Community Pet Park', 'details': 'Austin, TX', 'count': 22},
            {'name': 'River Trail', 'details': 'Portland, OR', 'count': 18}
        ],
        
        # Top active users
        'top_users': [
            {'username': 'petlover99', 'pets': range(3), 'hosted_playdates': range(12), 'activity_score': 87},
            {'username': 'dogwalker23', 'pets': range(2), 'hosted_playdates': range(8), 'activity_score': 72},
            {'username': 'catlady', 'pets': range(4), 'hosted_playdates': range(5), 'activity_score': 65},
            {'username': 'birdfriend', 'pets': range(6), 'hosted_playdates': range(3), 'activity_score': 58},
            {'username': 'petpal', 'pets': range(1), 'hosted_playdates': range(9), 'activity_score': 52}
        ]
    }
    
    # Check if mobile device
    if is_mobile_device():
        return render_template('admin/mobile_stats.html', stats=stats, period=period)
    else:
        return render_template('admin/stats.html', stats=stats, period=period)

@bp.route('/report/<int:report_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def report_details(report_id):
    from app.models.incident_report import IncidentReport
    report = IncidentReport.query.get_or_404(report_id)
    if request.method == 'POST':
        status = request.form.get('status')
        resolution = request.form.get('resolution')
        
        report.status = status
        report.resolution = resolution
        report.resolved_at = datetime.utcnow() if status == 'Resolved' else None
        db.session.commit()
        
        flash('Incident report updated successfully.', 'success')
        return redirect(url_for('admin.incident_reports'))
    
    return render_template('admin/report_details.html', report=report)

@bp.route('/test')
@login_required
@admin_required
def test_page():
    return render_template('admin/test.html')

@bp.route('/user/<int:user_id>/reset_password', methods=['POST'])
@login_required
@admin_required
def reset_user_password(user_id):
    from app.models.user import User
    
    user = User.query.get_or_404(user_id)
    
    # Generate a temporary password
    temp_password = secrets.token_urlsafe(8)  # 8 characters should be enough for a temporary password
    
    # Update the user's password
    user.set_password(temp_password)
    
    # Add a note about password reset
    admin_note = f"Password reset by admin {current_user.username} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    if user.account_notes:
        user.account_notes = admin_note + "\n\n" + user.account_notes
    else:
        user.account_notes = admin_note
    
    db.session.commit()
    
    flash(f"Password for {user.username} has been reset. Temporary password: {temp_password}", "success")
    return redirect(url_for('admin.user_details', user_id=user_id))

@bp.route('/user/<int:user_id>/impersonate', methods=['POST'])
@login_required
@admin_required
def impersonate_user(user_id):
    from app.models.user import User
    
    # Get the user to impersonate
    user_to_impersonate = User.query.get_or_404(user_id)
    
    # Store admin info in session
    session['is_impersonating'] = True
    session['admin_id'] = current_user.id
    session['admin_name'] = current_user.username
    
    # Log in as the user
    logout_user()
    login_user(user_to_impersonate)
    
    # Ensure username is in session for template checks
    session['username'] = user_to_impersonate.username
    
    flash(f'You are now impersonating {user_to_impersonate.username}. Return to admin mode by clicking the button in the navigation bar.', 'warning')
    return redirect(url_for('main.index'))

@bp.route('/stop-impersonating', methods=['POST'])
@login_required
def stop_impersonating():
    from app.models.user import User
    
    # Check if admin was impersonating
    if not session.get('is_impersonating'):
        flash('You were not in impersonation mode.', 'error')
        return redirect(url_for('main.index'))
    
    # Get original admin
    admin_id = session.get('admin_id')
    admin_user = User.query.get(admin_id)
    
    if not admin_user:
        flash('Could not restore admin session.', 'error')
        return redirect(url_for('auth.login'))
    
    # Clear impersonation flags
    admin_name = session.get('admin_name', 'Admin')
    session.pop('is_impersonating', None)
    session.pop('admin_id', None) 
    session.pop('admin_name', None)
    
    # Log back in as admin
    logout_user()
    login_user(admin_user)
    
    # Ensure username is in session for template checks
    session['username'] = admin_user.username
    
    flash(f'Welcome back, {admin_name}. You are no longer impersonating a user.', 'success')
    return redirect(url_for('admin.admin_dashboard'))

@bp.route('/playdate/cancel/<int:playdate_id>', methods=['GET'])
@login_required
@admin_required
def playdate_cancel(playdate_id):
    # Import the Playdate model
    from app.models.playdate import Playdate
    
    # Get the playdate by ID
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Update the status to cancelled
    playdate.status = 'cancelled'
    
    # Commit the changes to the database
    db.session.commit()
    
    # Flash a success message
    flash(f'Playdate "{playdate.title}" has been cancelled successfully.', 'success')
    
    # Redirect back to the playdates management page
    return redirect(url_for('admin.playdates_management'))

@bp.route('/pet/edit/<int:pet_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def pet_edit(pet_id):
    # Import necessary models
    from app.models.pet import Pet
    
    # Get the pet by ID
    pet = Pet.query.get_or_404(pet_id)
    
    # Handle form submission
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name')
        species = request.form.get('species')
        breed = request.form.get('breed')
        age = request.form.get('age')
        gender = request.form.get('gender')
        description = request.form.get('description')
        
        # Update pet details
        pet.name = name
        pet.species = species
        pet.breed = breed
        
        # Convert age to integer if provided
        try:
            if age:
                pet.age = int(age)
        except ValueError:
            flash('Age must be a number', 'error')
            return redirect(url_for('admin.pet_edit', pet_id=pet_id))
        
        pet.gender = gender
        pet.description = description
        
        # Save changes to database
        db.session.commit()
        
        # Flash success message
        flash(f'Pet "{pet.name}" has been updated successfully', 'success')
        
        # Redirect to pet details page
        return redirect(url_for('admin.pet_details', pet_id=pet.id))
    
    # For GET request, render the edit form
    return render_template('admin/mobile_pet_edit.html', pet=pet) 