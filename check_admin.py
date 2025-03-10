from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    # Check all users with is_admin=True
    admin_users = User.query.filter_by(is_admin=True).all()
    print(f"Found {len(admin_users)} admin users:")
    for user in admin_users:
        print(f"- Username: {user.username}, Email: {user.email}, Is Admin: {user.is_admin}")
    
    # Check specific 'admin' user
    admin_user = User.query.filter_by(username='admin').first()
    if admin_user:
        print(f"\nChecking 'admin' user:")
        print(f"- Username: {admin_user.username}")
        print(f"- Email: {admin_user.email}")
        print(f"- Is Admin: {admin_user.is_admin}")
    else:
        print("\nNo user with username 'admin' found") 