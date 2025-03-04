import pytest
from flask import url_for
from app import create_app, db
from app.models.user import User
from app.models.incident_report import IncidentReport
from datetime import datetime

@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def admin_user(app):
    user = User(
        username='admin',
        email='admin@example.com',
        is_admin=True,
        account_status='active'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user

@pytest.fixture
def regular_user(app):
    user = User(
        username='user',
        email='user@example.com',
        is_admin=False,
        account_status='active'
    )
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    return user

def test_admin_login(client, admin_user):
    """Test that admin can log in successfully"""
    response = client.post('/auth/login', data={
        'username': 'admin',
        'password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Welcome back' in response.data

def test_admin_dashboard_access(client, admin_user):
    """Test that admin can access the dashboard"""
    # Login as admin
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'password123'
    })
    
    # Try to access admin dashboard
    response = client.get('/admin/')
    assert response.status_code == 200
    assert b'Admin Dashboard' in response.data

def test_regular_user_dashboard_access(client, regular_user):
    """Test that regular user cannot access admin dashboard"""
    # Login as regular user
    client.post('/auth/login', data={
        'username': 'user',
        'password': 'password123'
    })
    
    # Try to access admin dashboard
    response = client.get('/admin/')
    assert response.status_code == 302  # Should redirect to home page
    assert b'You do not have permission' in response.data

def test_admin_dashboard_data(client, admin_user):
    """Test that admin dashboard shows correct data"""
    # Create some test data
    incident = IncidentReport(
        reporter_id=admin_user.id,
        incident_type='safety',
        description='Test incident',
        severity='low',
        status='Pending'
    )
    db.session.add(incident)
    db.session.commit()
    
    # Login as admin
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'password123'
    })
    
    # Access admin dashboard
    response = client.get('/admin/')
    assert response.status_code == 200
    assert b'1' in response.data  # Should show 1 pending report

def test_admin_navigation(client, admin_user):
    """Test that admin navigation menu is visible to admin users"""
    # Login as admin
    client.post('/auth/login', data={
        'username': 'admin',
        'password': 'password123'
    })
    
    # Check if admin link is in navigation
    response = client.get('/')
    assert response.status_code == 200
    assert b'Admin Panel' in response.data 