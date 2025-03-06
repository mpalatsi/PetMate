from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_socketio import SocketIO
import os
import logging
from config import Config
from flask_login import LoginManager

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Do NOT monkey patch here - it's already done in wsgi.py
logger.info("Using gevent for WebSocket support")

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# Initialize SocketIO
# Don't specify 'async_mode' here - it will be set in create_app
socketio = SocketIO(
    cors_allowed_origins="*", 
    logger=True, 
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))

def create_app(config_class=Config):
    """
    Application factory function to create and configure the Flask app
    
    Args:
        config_class: Configuration class to use (default: Config)
    
    Returns:
        Flask application instance
    """
    # Explicitly set template_folder to app/templates
    template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    app = Flask(__name__, 
                static_folder='static', 
                static_url_path='/static',
                template_folder=template_folder)
    app.config.from_object(config_class)
    
    # Print template folder location for debugging
    print(f"Flask template folders:")
    print(f"1. app.template_folder = {app.template_folder}")
    print(f"2. app.jinja_loader.searchpath = {app.jinja_loader.searchpath}")
    print(f"Current working directory: {os.getcwd()}")
    
    # Initialize extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'error'
    
    # Initialize SocketIO with best settings for WebSocket support
    # First try with gevent, fall back to default if not available
    try:
        import gevent
        socketio.init_app(
            app,
            async_mode='gevent',
            cors_allowed_origins="*",
            logger=True,
            engineio_logger=True,
            ping_timeout=60,
            ping_interval=25
        )
        logger.info(f"SocketIO initialized with gevent async_mode")
    except ImportError:
        # Fall back to default async_mode
        socketio.init_app(
            app,
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
    
    from app.routes.safety import bp as safety_bp
    app.register_blueprint(safety_bp)
    
    from app.routes.admin import bp as admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Register WebSocket events
    from app.routes.websockets import register_socket_events
    register_socket_events(socketio)
    
    # Register CLI commands
    from app.commands import create_admin_command
    app.cli.add_command(create_admin_command)
    
    # Register template filters
    from app.utils.helpers import format_datetime
    app.jinja_env.filters['datetime'] = format_datetime
    
    # Add a function to get file URLs in templates
    from app.utils.helpers import get_file_url
    app.jinja_env.globals.update(get_file_url=get_file_url)
    
    # Define a get_current_user function for templates
    def get_current_user():
        from flask_login import current_user
        return current_user
    
    # Add get_current_user to Jinja's globals
    app.jinja_env.globals.update(get_current_user=get_current_user)
    
    @app.context_processor
    def inject_user():
        """
        Inject the current user into all templates
        """
        from flask_login import current_user
        return {'current_user': current_user}
    
    @app.context_processor
    def inject_api_keys():
        """Inject API keys into all templates"""
        return {
            'google_maps_api_key': app.config['GOOGLE_MAPS_API_KEY']
        }
    
    # Import all models in the correct order
    with app.app_context():
        from app.models.user import User
        from app.models.pet import Pet
        from app.models.playdate import Playdate
        from app.models.message import Message
        from app.models.review import Review
        from app.models.playdate_photo import PlaydatePhoto
        from app.models.gallery_photo import GalleryPhoto
        from app.models.playdate_message import PlaydateMessage
        from app.models.emergency_contact import EmergencyContact
        from app.models.incident_report import IncidentReport
        from app.models.user_verification import UserVerification
    
    return app 