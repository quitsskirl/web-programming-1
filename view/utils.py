# =============================================================================
# SHARED UTILITIES - utils.py
# =============================================================================
# Common helper functions used across multiple route files.
# Import these in your routes instead of duplicating code.
#
# Usage:
#   from routs.utils import get_current_user, login_required
# =============================================================================

from flask import request, redirect, url_for, jsonify, current_app
from functools import wraps
import jwt
import os


# =============================================================================
# CONSTANTS
# =============================================================================
# JWT Configuration
JWT_ALGORITHM = 'HS256'
DEFAULT_SECRET = 'your-secret-key-change-in-production'

# Cookie settings
COOKIE_NAME = 'jwt_token'
COOKIE_MAX_AGE = 86400  # 24 hours in seconds

# Error messages
ERROR_TOKEN_MISSING = "Token is missing"
ERROR_TOKEN_EXPIRED = "Token has expired"
ERROR_TOKEN_INVALID = "Invalid token"
ERROR_ACCESS_DENIED = "Access denied"
ERROR_DB_UNAVAILABLE = "Database unavailable"


# =============================================================================
# AUTHENTICATION HELPERS
# =============================================================================
def get_jwt_secret():
    """
    Get JWT secret key from app config or environment.
    
    Returns:
        str: The JWT secret key
    """
    try:
        return current_app.config.get('JWT_SECRET_KEY', DEFAULT_SECRET)
    except RuntimeError:
        # Outside application context
        return os.getenv('JWT_SECRET_KEY', DEFAULT_SECRET)


def get_current_user():
    """
    Get current user from JWT token.
    
    Checks for token in:
    1. Cookies (for page routes)
    2. Authorization header (for API routes)
    3. Query parameters (fallback)
    
    Returns:
        dict: User payload from JWT token, or None if not authenticated
    
    Example:
        user = get_current_user()
        if user:
            username = user.get('username')
            role = user.get('role')
    """
    token = None
    
    # Method 1: Check cookie first (for page routes)
    token = request.cookies.get(COOKIE_NAME)
    
    # Method 2: Check Authorization header (for API routes)
    if not token and 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    
    # Method 3: Check query parameter (fallback)
    if not token:
        token = request.args.get('token')
    
    if not token:
        return None
    
    try:
        secret_key = get_jwt_secret()
        payload = jwt.decode(token, secret_key, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_user_role():
    """
    Get the current user's role.
    
    Returns:
        str: 'student', 'professional', or None if not authenticated
    """
    user = get_current_user()
    return user.get('role') if user else None


def get_username():
    """
    Get the current user's username.
    
    Returns:
        str: Username or None if not authenticated
    """
    user = get_current_user()
    return user.get('username') if user else None


def is_authenticated():
    """
    Check if user is authenticated.
    
    Returns:
        bool: True if user is logged in
    """
    return get_current_user() is not None


def is_student():
    """
    Check if current user is a student.
    
    Returns:
        bool: True if user is a student
    """
    return get_user_role() == 'student'


def is_professional():
    """
    Check if current user is a professional.
    
    Returns:
        bool: True if user is a professional
    """
    return get_user_role() == 'professional'


# =============================================================================
# ROUTE DECORATORS
# =============================================================================
def login_required(f):
    """
    Decorator for routes that require authentication.
    Redirects to student login if not authenticated.
    
    Usage:
        @login_required
        def my_route():
            # User is guaranteed to be logged in here
            username = request.current_user.get('username')
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('login_st.login_student_page'))
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


def student_required(f):
    """
    Decorator for routes that require student role.
    Redirects to student login if not authenticated or not a student.
    
    Usage:
        @student_required
        def student_only_route():
            # Only students can access this
            pass
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('login_st.login_student_page'))
        if user.get('role') != 'student':
            return jsonify({"message": ERROR_ACCESS_DENIED}), 403
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


def professional_required(f):
    """
    Decorator for routes that require professional role.
    Redirects to professional login if not authenticated or not a professional.
    
    Usage:
        @professional_required
        def professional_only_route():
            # Only professionals can access this
            pass
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('login_pf.login_professional_page'))
        if user.get('role') != 'professional':
            return jsonify({"message": ERROR_ACCESS_DENIED}), 403
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


# =============================================================================
# FILE UPLOAD HELPERS
# =============================================================================
ALLOWED_PDF_EXTENSIONS = {'pdf'}
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename, allowed_extensions=None):
    """
    Check if a file has an allowed extension.
    
    Args:
        filename: The filename to check
        allowed_extensions: Set of allowed extensions (default: PDF)
    
    Returns:
        bool: True if file extension is allowed
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_PDF_EXTENSIONS
    
    if not filename or '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions


def allowed_pdf(filename):
    """Check if file is a PDF."""
    return allowed_file(filename, ALLOWED_PDF_EXTENSIONS)


def allowed_image(filename):
    """Check if file is an image."""
    return allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS)


# =============================================================================
# VALIDATION HELPERS
# =============================================================================
def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present and non-empty.
    
    Args:
        data: Dictionary of data to validate
        required_fields: List of required field names
    
    Returns:
        tuple: (is_valid, missing_fields)
    
    Example:
        is_valid, missing = validate_required_fields(
            {'name': 'John', 'email': ''},
            ['name', 'email', 'password']
        )
        # is_valid = False, missing = ['email', 'password']
    """
    missing = []
    for field in required_fields:
        value = data.get(field)
        if not value or (isinstance(value, str) and not value.strip()):
            missing.append(field)
    
    return len(missing) == 0, missing


def validate_email(email):
    """
    Simple email validation.
    
    Args:
        email: Email string to validate
    
    Returns:
        bool: True if email looks valid
    """
    if not email or not isinstance(email, str):
        return False
    return '@' in email and '.' in email.split('@')[-1]


def validate_password(password, min_length=4):
    """
    Validate password meets minimum requirements.
    
    Args:
        password: Password string to validate
        min_length: Minimum password length (default: 4)
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not password:
        return False, "Password is required"
    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters"
    return True, None


# =============================================================================
# DATABASE HELPERS
# =============================================================================
def get_db_collection(collection_name):
    """
    Safely get a MongoDB collection from the app.
    
    Args:
        collection_name: Name of the collection ('students', 'professionals', etc.)
    
    Returns:
        Collection object or None if unavailable
    """
    try:
        from app import students, professionals, appointments, resources
        from app import support_tickets, notifications, event_images, feedback
        
        collections = {
            'students': students,
            'professionals': professionals,
            'appointments': appointments,
            'resources': resources,
            'support_tickets': support_tickets,
            'notifications': notifications,
            'event_images': event_images,
            'feedback': feedback,
        }
        return collections.get(collection_name)
    except ImportError:
        return None
