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
    
    # Collect statistics in a dictionary
    stats = {
        'total_users': User.query.count(),
        'total_pets': Pet.query.count(),
        'total_playdates': Playdate.query.count(),
        'total_reports': IncidentReport.query.count()
    }
    
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_users=recent_users)

@bp.route('/users')
@login_required
@admin_required
def user_management():
    from app.models.user import User
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=20)
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
            'pets': pets
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
    
    return redirect(url_for('admin.user_details', user_id=user_id))

@bp.route('/pets')
@login_required
@admin_required
def pets_management():
    from app.models.pet import Pet
    page = request.args.get('page', 1, type=int)
    pets = Pet.query.paginate(page=page, per_page=20)
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
    page = request.args.get('page', 1, type=int)
    playdates = Playdate.query.paginate(page=page, per_page=20)
    return render_template('admin/playdates.html', playdates=playdates)

@bp.route('/playdate/<int:playdate_id>')
@login_required
@admin_required
def playdate_details(playdate_id):
    from app.models.playdate import Playdate
    playdate = Playdate.query.get_or_404(playdate_id)
    return render_template('admin/playdate_details.html', playdate=playdate)

@bp.route('/playdate/<int:playdate_id>/update', methods=['POST'])
@login_required
@admin_required
def update_playdate_status(playdate_id):
    from app.models.playdate import Playdate
    
    playdate = Playdate.query.get_or_404(playdate_id)
    action = request.form.get('action')
    
    if action == 'cancel':
        playdate.status = 'cancelled'
        admin_note = f"Cancelled by admin {current_user.username} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        if playdate.admin_notes:
            playdate.admin_notes = admin_note + "\n\n" + playdate.admin_notes
        else:
            playdate.admin_notes = admin_note
            
        db.session.commit()
        flash('Playdate has been cancelled.', 'success')
    
    return redirect(url_for('admin.playdate_details', playdate_id=playdate_id))

@bp.route('/reports')
@login_required
@admin_required
def incident_reports():
    from app.models.incident_report import IncidentReport
    page = request.args.get('page', 1, type=int)
    reports = IncidentReport.query.order_by(IncidentReport.created_at.desc()).paginate(page=page, per_page=20)
    return render_template('admin/reports.html', reports=reports)

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