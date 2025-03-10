from app import create_app, db
from app.models.user import User

app = create_app()

with app.app_context():
    user = User.query.filter_by(username='admin').first()
    if user:
        print(f"Found user: {user.username}")
        print(f"Current admin status: {user.is_admin}")
        user.is_admin = True
        db.session.commit()
        print(f"Updated admin status: {user.is_admin}")
    else:
        print("User 'admin' not found") 