# This file is intentionally left empty to mark the directory as a Python package 

from app import db

# Import User first since other models depend on it
from .user import User

# Then import other models that depend on User
from .pet import Pet
from .playdate import Playdate
from .message import Message
from .review import Review
from .playdate_photo import PlaydatePhoto
from .gallery_photo import GalleryPhoto
from .playdate_message import PlaydateMessage
from .emergency_contact import EmergencyContact
from .incident_report import IncidentReport
from .user_verification import UserVerification

# Export all models
__all__ = [
    'User',
    'Pet',
    'Playdate',
    'Message',
    'Review',
    'PlaydatePhoto',
    'GalleryPhoto',
    'PlaydateMessage',
    'EmergencyContact',
    'IncidentReport',
    'UserVerification'
] 