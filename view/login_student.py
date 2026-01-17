# =============================================================================
# STUDENT LOGIN ROUTE - login_student.py
# =============================================================================
# Handles student authentication (login).
#
# URL: /login-student
# TEMPLATE: loginST.html
#
# AUTHENTICATION FLOW:
# 1. User visits /login-student (GET) -> sees login form
# 2. User enters credentials and submits form (POST)
# 3. Server calls the JWT API at /api/login/student
# 4. If valid: token stored in cookie, redirect to /home
# 5. If invalid: flash error, stay on login page
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, make_response
import requests  # Used to call our own API internally

# Create Blueprint
login_st_bp = Blueprint('login_st', __name__)


# =============================================================================
# CONSTANTS
# =============================================================================
API_TIMEOUT = 5  # Seconds to wait for API response
COOKIE_MAX_AGE = 86400  # 24 hours in seconds

# Error messages
ERROR_INVALID = "Invalid username or password"
ERROR_MISSING = "Please enter username and password"
ERROR_UNAVAILABLE = "Login service unavailable. Please try again."


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def validate_login_input(username, password):
    """
    Validate that username and password are provided.
    
    Args:
        username: The submitted username
        password: The submitted password
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not username or not password:
        return False, ERROR_MISSING
    return True, None


# =============================================================================
# ROUTE HANDLERS
# =============================================================================
@login_st_bp.route('/login-student', methods=['GET', 'POST'])
def login_student_page():
    """
    Display and process student login form.
    
    URL: http://localhost:5000/login-student
    
    GET: Display the login form
    POST: Process login credentials
    
    Form Data Expected:
        - username: Student's username
        - password: Student's password
    
    Returns:
        GET: Rendered loginST.html template
        POST Success: Redirect to /home with JWT cookie set
        POST Failure: Re-render login page with error message
    """
    if request.method == 'POST':
        # Get form data
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Validate input
        is_valid, error_msg = validate_login_input(username, password)
        if not is_valid:
            flash(error_msg)
            return render_template('loginST.html')
        
        # Call our JWT login API
        try:
            response = requests.post(
                request.url_root + 'api/login/student',
                json={"username": username, "password": password},
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                # Login successful - extract JWT token
                data = response.json()
                token = data.get('token')
                
                # Store user info in session (optional, for easy access)
                session['user'] = {'role': 'student', 'username': username}
                
                # Create redirect response
                resp = make_response(redirect(url_for('home.home_page')))
                
                # Store JWT token in secure HTTP-only cookie
                resp.set_cookie(
                    'jwt_token', 
                    token, 
                    httponly=True, 
                    secure=False, 
                    samesite='Lax', 
                    max_age=COOKIE_MAX_AGE
                )
                return resp
            else:
                flash(ERROR_INVALID)
                return render_template('loginST.html')
                
        except Exception as e:
            flash(ERROR_UNAVAILABLE)
            return render_template('loginST.html')
    
    # GET request - show login form
    return render_template('loginST.html')
