import click
from flask.cli import with_appcontext
from app.models.user import User
from app import db
from datetime import datetime

@click.command('create-admin')
@click.argument('username')
@click.argument('email')
@click.argument('password')
@with_appcontext
def create_admin_command(username, email, password):
    """Create a new admin user."""
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        click.echo(f'User {username} already exists.')
        return
    
    user = User(
        username=username,
        email=email,
        is_admin=True,
        account_status='active',
        last_login=datetime.utcnow()
    )
    user.set_password(password)
    
    try:
        db.session.add(user)
        db.session.commit()
        click.echo(f'Admin user {username} created successfully!')
    except Exception as e:
        db.session.rollback()
        click.echo(f'Error creating admin user: {e}') 