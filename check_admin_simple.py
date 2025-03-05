from app import create_app, db
from app.models.user import User
from datetime import datetime

app = create_app()

with app.app_context():
    # Check if admin user exists
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print(f"Admin user exists with username: {admin.username}")
        print(f"Admin is_admin flag: {admin.is_admin}")
        print(f"Admin status: {admin.account_status}")
        print(f"Password hash: {admin.password_hash[:30]}...")
        
        # Check if we need to update the password
        admin.set_password('adminpass')
        db.session.commit()
        print("Updated admin password to 'adminpass'")
    else:
        # Create new admin user
        print("Creating new admin user...")
        new_admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True,
            account_status='active',
            created_at=datetime.utcnow()
        )
        new_admin.set_password('adminpass')
        db.session.add(new_admin)
        db.session.commit()
        print("Created new admin user with credentials:")
        print("Username: admin")
        print("Password: adminpass") 