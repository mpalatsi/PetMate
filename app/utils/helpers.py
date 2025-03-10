from werkzeug.utils import secure_filename
import os
import time
import base64
from datetime import datetime
import uuid
import re
import requests
from functools import lru_cache
from math import radians, sin, cos, sqrt, atan2

def allowed_file(filename, allowed_extensions=None):
    """
    Check if a file has an allowed extension
    
    Args:
        filename (str): The filename to check
        allowed_extensions (set): Set of allowed extensions (default: images)
    
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, upload_folder, base_filename=None, force_extension=None):
    """
    Save an uploaded file with a secure filename
    
    Args:
        file: The file object from request.files
        upload_folder (str): The folder to save the file to
        base_filename (str, optional): Base name for the file (without extension)
        force_extension (str, optional): If provided, use this extension instead of the original
    
    Returns:
        str: The filename of the saved file
    """
    # Create the upload folder if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)
    
    # Get a secure filename
    filename = secure_filename(file.filename)
    
    # Get the file extension
    if force_extension:
        extension = f".{force_extension.lstrip('.')}"
    else:
        _, extension = os.path.splitext(filename)
    
    # Generate a unique filename if base_filename is not provided
    if not base_filename:
        base_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Combine base filename with extension
    new_filename = f"{base_filename}{extension}"
    
    # Save the file
    file_path = os.path.join(upload_folder, new_filename)
    file.save(file_path)
    
    return new_filename

def save_base64_image(base64_data, upload_folder, base_filename=None, force_extension=None):
    """
    Save a base64 encoded image to a file
    
    Args:
        base64_data (str): The base64 encoded image data
        upload_folder (str): The folder to save the file to
        base_filename (str, optional): Base name for the file (without extension)
        force_extension (str, optional): If provided, use this extension instead of the detected format
    
    Returns:
        str: The filename of the saved file
    """
    # Remove 'app/' prefix if it exists
    if upload_folder.startswith('app/'):
        upload_folder = upload_folder[4:]
    
    # Create the upload folder if it doesn't exist
    os.makedirs(upload_folder, exist_ok=True)
    
    # Extract the image data and format from the base64 string
    if ',' in base64_data:
        header, encoded = base64_data.split(',', 1)
        # Extract the image format from the header
        match = re.search(r'data:image/(\w+);', header)
        if match:
            image_format = match.group(1)
        else:
            image_format = 'png'  # Default to PNG if format not found
    else:
        encoded = base64_data
        image_format = 'png'  # Default to PNG
    
    # Use forced extension if provided
    if force_extension:
        image_format = force_extension.lstrip('.')
    
    # Decode the base64 data
    image_data = base64.b64decode(encoded)
    
    # Generate a unique filename if base_filename is not provided
    if not base_filename:
        base_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Combine base filename with extension
    new_filename = f"{base_filename}.{image_format}"
    
    # Save the file
    file_path = os.path.join(upload_folder, new_filename)
    with open(file_path, 'wb') as f:
        f.write(image_data)
    
    return new_filename

def format_datetime(value, format='%Y-%m-%d %H:%M'):
    """
    Format a datetime object to a string
    
    Args:
        value: The datetime object to format
        format (str): The format string
    
    Returns:
        str: The formatted datetime string
    """
    if value is None:
        return ""
    return value.strftime(format)

def get_file_url(filename, folder):
    """
    Get the URL for a file
    
    Args:
        filename (str): The filename
        folder (str): The folder name (e.g., 'profile_pictures', 'pet_images')
    
    Returns:
        str: The URL for the file
    """
    if not filename:
        return None
    
    # Remove any static folder prefixes to ensure compatibility with the consolidated folder
    if folder.startswith('app/static/'):
        folder = folder[11:]
    elif folder.startswith('/app/static/'):
        folder = folder[12:]
    elif folder.startswith('/app/app/static/'):
        folder = folder[13:]
    elif folder.startswith('static/'):
        folder = folder[7:]
    
    return f"/static/{folder}/{filename}"

# Geocoding functions for location-based search
@lru_cache(maxsize=128)  # Cache results to avoid redundant API calls
def geocode_address(address):
    """
    Convert an address or zipcode into latitude and longitude coordinates
    using a geocoding service.
    
    Args:
        address (str): Address string or zipcode
        
    Returns:
        tuple: (latitude, longitude) or (None, None) if geocoding fails
    """
    # Use Google Maps API for geocoding if API key is available
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    
    if not api_key:
        print("Warning: GOOGLE_MAPS_API_KEY not set, geocoding disabled")
        return None, None
    
    try:
        # Format the request URL
        base_url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {
            "address": address,
            "key": api_key
        }
        
        # Send the request
        response = requests.get(base_url, params=params)
        data = response.json()
        
        # Check if the request was successful
        if data['status'] == 'OK':
            # Extract coordinates from the response
            location = data['results'][0]['geometry']['location']
            return location['lat'], location['lng']
        else:
            print(f"Geocoding error: {data['status']}")
            return None, None
            
    except Exception as e:
        print(f"Error during geocoding: {str(e)}")
        return None, None

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Calculate the distance in miles between two points using the Haversine formula.
    
    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point
        
    Returns:
        float: Distance in miles
    """
    # Convert latitude and longitude from degrees to radians
    lat1, lon1 = map(radians, [lat1, lon1])
    lat2, lon2 = map(radians, [lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    
    # Earth radius in miles
    radius = 3959
    
    # Calculate distance
    distance = radius * c
    return distance

def is_mobile_device(request):
    """
    Enhanced detection for mobile devices with more aggressive desktop detection
    to ensure desktop browsers always get desktop version.
    """
    # First check user agent as the most reliable indicator
    user_agent = request.headers.get('User-Agent', '').lower()
    
    # Definite desktop indicators - these should always get desktop version
    desktop_indicators = [
        'windows nt', 'macintosh', 'win64', 'x11',
        'windows', 'ubuntu', 'debian', 'fedora', 'mint',
        'msie', 'trident', 'edge/',
    ]
    
    # If any desktop indicator found, it's definitely a desktop
    for indicator in desktop_indicators:
        if indicator in user_agent:
            # Override - this is definitely a desktop
            return False
    
    # Check for mobile indicators
    mobile_indicators = [
        'android', 'webos', 'iphone', 'ipad', 'ipod', 'blackberry', 'windows phone',
        'mobile', 'opera mini', 'opera mobi', 'fennec', 'tablet'
    ]
    
    # If any mobile indicator found, it's a mobile device
    for indicator in mobile_indicators:
        if indicator in user_agent:
            return True
            
    # Check viewport size if available (from a cookie or header)
    viewport_width = request.cookies.get('viewportWidth', '')
    try:
        if viewport_width and int(viewport_width) < 768:
            return True
    except (ValueError, TypeError):
        pass
    
    # Default to desktop for unknown agents (safer assumption)
    return False 