import unittest
import os
import sys
import io
from unittest.mock import patch, MagicMock
from PIL import Image

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User
from app.models.gallery_photo import GalleryPhoto
from app.models.photo_like import PhotoLike
from app.models.photo_comment import PhotoComment
from app.models.photo_report import PhotoReport
from app.models.pet import Pet
from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    UPLOAD_FOLDER = '/tmp/petmate_test_uploads'


class TestGallery(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        
        # Create upload directory if it doesn't exist
        os.makedirs(os.path.join(TestConfig.UPLOAD_FOLDER, 'gallery_photos'), exist_ok=True)
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            user = User(
                username='testuser',
                email='test@example.com',
                phone_number='1234567890',
                first_name='Test',
                last_name='User'
            )
            user.set_password('password123')
            
            # Create admin user
            admin = User(
                username='admin',
                email='admin@example.com',
                phone_number='0987654321',
                first_name='Admin',
                last_name='User',
                is_admin=True
            )
            admin.set_password('adminpass')
            
            # Create test pet
            pet = Pet(
                name='Buddy',
                species='Dog',
                breed='Golden Retriever',
                age=3,
                owner_id=1
            )
            
            db.session.add(user)
            db.session.add(admin)
            db.session.add(pet)
            db.session.commit()
            
            # Add test photo
            photo = GalleryPhoto(
                user_id=1,
                pet_id=1,
                filename='test_photo.jpg',
                title='Test Photo',
                description='This is a test photo',
                is_public=True
            )
            db.session.add(photo)
            db.session.commit()
    
    def tearDown(self):
        """Clean up after tests"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        
        # Clean up test upload folder
        import shutil
        if os.path.exists(TestConfig.UPLOAD_FOLDER):
            shutil.rmtree(TestConfig.UPLOAD_FOLDER)
    
    def login(self, username='testuser', password='password123'):
        """Helper function to log in"""
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)
    
    def logout(self):
        """Helper function to log out"""
        return self.client.get('/logout', follow_redirects=True)
    
    def create_test_image(self):
        """Helper function to create a test image file"""
        image = Image.new('RGB', (100, 100), color='red')
        img_io = io.BytesIO()
        image.save(img_io, 'JPEG')
        img_io.seek(0)
        return img_io
    
    def test_gallery_access(self):
        """Test access to gallery page"""
        # Try accessing without login
        response = self.client.get('/gallery', follow_redirects=True)
        self.assertIn(b'Please log in', response.data)
        
        # Login and access
        self.login()
        response = self.client.get('/gallery')
        self.assertEqual(response.status_code, 200)
    
    def test_upload_photo(self):
        """Test photo upload functionality"""
        self.login()
        
        # Create mock image
        img_io = self.create_test_image()
        
        # Upload photo
        response = self.client.post('/gallery/upload', data={
            'photo': (img_io, 'test_upload.jpg'),
            'title': 'Uploaded Test Photo',
            'description': 'This is an uploaded test photo',
            'pet_id': '1',
            'is_public': 'true'
        }, content_type='multipart/form-data', follow_redirects=True)
        
        self.assertIn(b'successfully', response.data)
        
        # Check if photo exists in database
        with self.app.app_context():
            photo = GalleryPhoto.query.filter_by(title='Uploaded Test Photo').first()
            self.assertIsNotNone(photo)
            self.assertEqual(photo.description, 'This is an uploaded test photo')
            self.assertEqual(photo.pet_id, 1)
            self.assertTrue(photo.is_public)
    
    def test_photo_privacy(self):
        """Test photo privacy settings"""
        self.login()
        
        # Create a private photo
        with self.app.app_context():
            photo = GalleryPhoto(
                user_id=1,
                filename='private_photo.jpg',
                title='Private Photo',
                is_public=False
            )
            db.session.add(photo)
            db.session.commit()
            private_photo_id = photo.id
        
        # View private photo as owner
        response = self.client.get(f'/gallery/photo/{private_photo_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Private Photo', response.data)
        
        # Logout and login as different user
        self.logout()
        self.login('admin', 'adminpass')
        
        # Try to view private photo as different user
        response = self.client.get(f'/gallery/photo/{private_photo_id}', follow_redirects=True)
        self.assertIn(b'do not have permission', response.data)
    
    def test_like_functionality(self):
        """Test photo liking functionality"""
        self.login()
        
        # Get photo ID
        with self.app.app_context():
            photo = GalleryPhoto.query.filter_by(title='Test Photo').first()
            photo_id = photo.id
        
        # Like the photo
        response = self.client.post(f'/gallery/photo/{photo_id}/like', headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['action'], 'liked')
        self.assertEqual(data['like_count'], 1)
        
        # Unlike the photo
        response = self.client.post(f'/gallery/photo/{photo_id}/like', headers={'X-Requested-With': 'XMLHttpRequest'})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['action'], 'unliked')
        self.assertEqual(data['like_count'], 0)
    
    def test_comment_functionality(self):
        """Test photo commenting functionality"""
        self.login()
        
        # Get photo ID
        with self.app.app_context():
            photo = GalleryPhoto.query.filter_by(title='Test Photo').first()
            photo_id = photo.id
        
        # Add a comment
        response = self.client.post(f'/gallery/photo/{photo_id}/comment', data={
            'comment': 'This is a test comment!'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'This is a test comment!', response.data)
        
        # Check if comment exists in database
        with self.app.app_context():
            comment = PhotoComment.query.filter_by(photo_id=photo_id).first()
            self.assertIsNotNone(comment)
            self.assertEqual(comment.comment, 'This is a test comment!')
            self.assertEqual(comment.user_id, 1)
    
    def test_report_functionality(self):
        """Test photo reporting functionality"""
        self.login()
        
        # Get photo ID
        with self.app.app_context():
            photo = GalleryPhoto.query.filter_by(title='Test Photo').first()
            photo_id = photo.id
        
        # Report the photo
        response = self.client.post(f'/gallery/photo/{photo_id}/report', data={
            'reason': 'inappropriate',
            'details': 'This is a test report'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Thank you for your report', response.data)
        
        # Check if report exists in database
        with self.app.app_context():
            report = PhotoReport.query.filter_by(photo_id=photo_id).first()
            self.assertIsNotNone(report)
            self.assertEqual(report.reason, 'inappropriate')
            self.assertEqual(report.details, 'This is a test report')
            self.assertEqual(report.user_id, 1)
    
    def test_photo_editing(self):
        """Test photo editing functionality"""
        self.login()
        
        # Get photo ID
        with self.app.app_context():
            photo = GalleryPhoto.query.filter_by(title='Test Photo').first()
            photo_id = photo.id
        
        # Edit the photo
        response = self.client.post(f'/gallery/photo/{photo_id}/edit', data={
            'title': 'Updated Test Photo',
            'description': 'This photo has been updated',
            'pet_id': '1'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'updated successfully', response.data)
        
        # Check if photo was updated in database
        with self.app.app_context():
            photo = GalleryPhoto.query.get(photo_id)
            self.assertEqual(photo.title, 'Updated Test Photo')
            self.assertEqual(photo.description, 'This photo has been updated')
    
    def test_photo_deletion(self):
        """Test photo deletion functionality"""
        self.login()
        
        # Get photo ID
        with self.app.app_context():
            photo = GalleryPhoto.query.filter_by(title='Test Photo').first()
            photo_id = photo.id
        
        # Delete the photo
        response = self.client.post(f'/gallery/photo/{photo_id}/delete', follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'deleted successfully', response.data)
        
        # Check if photo was deleted from database
        with self.app.app_context():
            photo = GalleryPhoto.query.get(photo_id)
            self.assertIsNone(photo)


if __name__ == '__main__':
    unittest.main() 