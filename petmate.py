from app import create_app, db
from app.models.user import User
from app.models.pet import Pet
from app.models.playdate import Playdate
from app.models.message import Message
from app.models.review import Review
from app.models.photo import PlaydatePhoto, GalleryPhoto
import os
from config import DevelopmentConfig, ProductionConfig, TestingConfig

# Determine which configuration to use based on environment variable
config_name = os.environ.get('FLASK_CONFIG', 'development')
config_map = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

# Create the Flask application
app = create_app(config_map.get(config_name, DevelopmentConfig))

@app.shell_context_processor
def make_shell_context():
    """
    Add database and models to the shell context for flask shell command
    """
    return {
        'db': db,
        'User': User,
        'Pet': Pet,
        'Playdate': Playdate,
        'Message': Message,
        'Review': Review,
        'PlaydatePhoto': PlaydatePhoto,
        'GalleryPhoto': GalleryPhoto
    }

@app.cli.command('create-tables')
def create_tables():
    """
    Create all database tables
    """
    db.create_all()
    print('Database tables created')

@app.cli.command('drop-tables')
def drop_tables():
    """
    Drop all database tables
    """
    db.drop_all()
    print('Database tables dropped')

@app.cli.command('seed-data')
def seed_data():
    """
    Seed the database with sample data
    """
    # Add sample users
    users = [
        User(username='john_doe', email='john@example.com', name='John Doe', 
             password_hash='pbkdf2:sha256:150000$abc123$abcdef123456789'),
        User(username='jane_smith', email='jane@example.com', name='Jane Smith',
             password_hash='pbkdf2:sha256:150000$def456$abcdef123456789')
    ]
    db.session.add_all(users)
    db.session.commit()
    
    # Add sample pets
    pets = [
        Pet(name='Buddy', species='Dog', breed='Golden Retriever', age=3, 
            size='Large', temperament='Friendly', owner_id=1),
        Pet(name='Max', species='Dog', breed='German Shepherd', age=2, 
            size='Large', temperament='Protective', owner_id=1),
        Pet(name='Whiskers', species='Cat', breed='Siamese', age=4, 
            size='Medium', temperament='Independent', owner_id=2)
    ]
    db.session.add_all(pets)
    db.session.commit()
    
    print('Sample data added to database')

if __name__ == '__main__':
    app.run(debug=True) 