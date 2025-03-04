from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from datetime import datetime
from functools import wraps

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
        
        print(f"Before template: User object type: {type(user)}")
        print(f"Before template: User object: {user}")
        print(f"Before template: User attributes: {dir(user)}")
        print(f"Before template: User reviews count: {len(user.reviews_received)}")
        
        # Create template context
        context = {'user': user}
        print(f"Template context: {context}")
        
        # Check if user is properly loaded
        if not isinstance(user, User):
            print("Warning: user is not a User instance")
            return "Error: Invalid user object", 500
        
        # Provide reference user ID for template fallbacks
        user_id_value = user.id
        
        response = render_template('admin/user_details.html', user=user, user_id=user_id_value)
        print(f"After template: User object type: {type(user)}")
        print(f"After template: User object: {user}")
        return response
        
    except Exception as e:
        print(f"Error in user_details: {str(e)}")
        db.session.rollback()
        return "An error occurred", 500

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