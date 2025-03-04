from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
import os
import logging
from config import Config

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

# Initialize SocketIO - use gevent as async_mode
socketio = SocketIO(async_mode='gevent')

def create_app(config_class=Config):
    """
    Application factory function to create and configure the Flask app
    
    Args:
        config_class: Configuration class to use (default: Config)
    
    Returns:
        Flask application instance
    """
    app = Flask(__name__, static_folder='../static', static_url_path='/static')
    app.config.from_object(config_class)
    
    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Initialize SocketIO with full configuration after app is created
    socketio.init_app(
        app, 
        async_mode='gevent',
        cors_allowed_origins="*", 
        logger=True, 
        engineio_logger=True,
        ping_timeout=60,
        ping_interval=25
    )
    logger.info(f"SocketIO initialized with async_mode: {socketio.async_mode}")
    
    # Create upload directories if they don't exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'profile_pictures'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'pet_images'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'playdate_photos'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'gallery'), exist_ok=True)
    
    # Register blueprints
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp)
    
    from app.routes.pets import bp as pets_bp
    app.register_blueprint(pets_bp)
    
    from app.routes.playdates import bp as playdates_bp
    app.register_blueprint(playdates_bp)
    
    from app.routes.messages import bp as messages_bp
    app.register_blueprint(messages_bp)
    
    from app.routes.reviews import bp as reviews_bp
    app.register_blueprint(reviews_bp)
    
    # Register WebSocket events
    from app.routes.websockets import register_socket_events
    register_socket_events(socketio)
    
    # Register template filters
    from app.utils.helpers import format_datetime
    app.jinja_env.filters['datetime'] = format_datetime
    
    # Add a function to get file URLs in templates
    from app.utils.helpers import get_file_url
    app.jinja_env.globals.update(get_file_url=get_file_url)
    
    # Define a get_current_user function for templates
    def get_current_user():
        from flask import session
        from app.models.user import User
        if 'username' in session:
            return User.query.filter_by(username=session['username']).first()
        return None
    
    # Add get_current_user to Jinja's globals
    app.jinja_env.globals.update(get_current_user=get_current_user)
    
    @app.context_processor
    def inject_user():
        """
        Inject the current user into all templates
        """
        from flask import session
        from app.models.user import User
        
        user = None
        if 'username' in session:
            user = User.query.filter_by(username=session['username']).first()
        
        return {'current_user': user}
    
    @app.context_processor
    def inject_api_keys():
        """Inject API keys into all templates"""
        return {
            'google_maps_api_key': app.config['GOOGLE_MAPS_API_KEY']
        }
    
    return app

# Import models to ensure they are registered with SQLAlchemy
from app.models.user import User
from app.models.pet import Pet
from app.models.playdate import Playdate
from app.models.message import Message
from app.models.review import Review
from app.models.photo import PlaydatePhoto
from app.models.gallery_photo import GalleryPhoto
from app.models.playdate_message import PlaydateMessage 