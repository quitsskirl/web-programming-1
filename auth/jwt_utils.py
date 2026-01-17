# =============================================================================
# JWT UTILITIES - auth/jwt_utils.py
# =============================================================================
# JWT token generation and verification functions.
#
# Usage:
#   from auth.jwt_utils import generate_token, token_required
# =============================================================================

from functools import wraps
from flask import request, jsonify, current_app
import jwt
import datetime


# =============================================================================
# TOKEN GENERATION
# =============================================================================
def generate_token(user_id, username, role="student"):
    """
    Create a JWT token containing user information.
    
    Args:
        user_id: MongoDB ObjectId (will be converted to string)
        username: User's username
        role: 'student' or 'professional'
    
    Returns:
        str: Encoded JWT token
    """
    payload = {
        "user_id": str(user_id),
        "username": username,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(
            hours=current_app.config.get("JWT_EXPIRATION_HOURS", 24)
        ),
        "iat": datetime.datetime.utcnow()
    }
    
    secret_key = current_app.config.get("JWT_SECRET_KEY", "your-secret-key")
    return jwt.encode(payload, secret_key, algorithm="HS256")


# =============================================================================
# TOKEN VERIFICATION DECORATOR
# =============================================================================
def token_required(f):
    """
    Decorator to protect routes that require authentication.
    
    Checks for JWT token in:
    1. Authorization header (Bearer token)
    2. Query parameter (?token=xxx)
    
    If valid, sets request.current_user to the decoded payload.
    
    Usage:
        @app.route("/protected")
        @token_required
        def protected_route():
            username = request.current_user.get('username')
            return jsonify({"message": f"Hello {username}!"})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Method 1: Check Authorization header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        # Method 2: Check query parameter
        if not token:
            token = request.args.get("token")

        # No token found
        if not token:
            return jsonify({"message": "Token is missing"}), 401

        # Verify token
        try:
            secret_key = current_app.config.get("JWT_SECRET_KEY", "your-secret-key")
            payload = jwt.decode(token, secret_key, algorithms=["HS256"])
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401

        return f(*args, **kwargs)
    return decorated


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_current_user_from_token():
    """
    Get current user from JWT token in request.
    
    Checks cookies, Authorization header, and query params.
    
    Returns:
        dict: User payload or None if not authenticated
    """
    token = None
    
    # Check cookie
    token = request.cookies.get('jwt_token')
    
    # Check Authorization header
    if not token and "Authorization" in request.headers:
        auth_header = request.headers["Authorization"]
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
    
    # Check query parameter
    if not token:
        token = request.args.get("token")
    
    if not token:
        return None
    
    try:
        secret_key = current_app.config.get("JWT_SECRET_KEY", "your-secret-key")
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def verify_token(token):
    """
    Verify a JWT token and return the payload.
    
    Args:
        token: JWT token string
    
    Returns:
        dict: Decoded payload or None if invalid
    """
    try:
        secret_key = current_app.config.get("JWT_SECRET_KEY", "your-secret-key")
        return jwt.decode(token, secret_key, algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None
