"""
=============================================================================
PROFESSOR LOGIN ROUTE - login_professional.py
=============================================================================
This file handles professor/professional authentication (login).

PURPOSE:
--------
- GET /login-professional  -> Display the login form
- POST /login-professional -> Process login credentials

URL: /login-professional

TEMPLATE: loginPF.html

AUTHENTICATION FLOW:
--------------------
1. User visits /login-professional (GET) -> sees login form
2. User enters credentials and submits form (POST)
3. Server calls the JWT API at /api/login/professional
4. If credentials valid:
   - API returns a JWT token with role='professional'
   - Token is stored in a secure HTTP-only cookie
   - User is redirected to /home-professor (NOT /home)
5. If invalid:
   - Flash message shows error
   - User stays on login page

KEY DIFFERENCE FROM STUDENT LOGIN:
----------------------------------
The only difference is the redirect destination:
- Students -> /home (student dashboard)
- Professors -> /home-professor (professor dashboard)

This ensures each user type sees their appropriate interface.
=============================================================================
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
import requests  # Used to call our own API internally

# Create a Blueprint named 'login_pf'
# Used in templates as: url_for('login_pf.login_professional_page')
login_pf_bp = Blueprint('login_pf', __name__)


@login_pf_bp.route('/login-professional')
def login_professional_page():
    """
    Display professor login form (GET request).
    
    URL: http://localhost:5000/login-professional
    
    Simply renders the login form. The actual authentication
    happens when the form is submitted (POST request).
    
    Returns:
        Rendered loginPF.html template
    """
    return render_template('loginPF.html')


@login_pf_bp.route('/login-professional', methods=['POST'])
def login_professional_post():
    """
    Process professor login (POST request).
    
    URL: http://localhost:5000/login-professional (POST)
    
    This function:
    1. Gets username/password from the submitted form
    2. Calls our JWT API to verify credentials
    3. If valid: stores token in cookie, redirects to professor home
    4. If invalid: shows error message, stays on login page
    
    Form Data Expected:
        - username: Professor's username
        - password: Professor's password
    
    Returns:
        - Success: Redirect to /home-professor with JWT cookie set
        - Failure: Re-render login page with error message
    """
    # Get form data
    username = request.form.get("username")
    password = request.form.get("password")

    # Call our JWT login API for professionals
    try:
        # Make internal API call to verify credentials
        response = requests.post(
            request.url_root + 'api/login/professional',  # http://localhost:5000/api/login/professional
            json={"username": username, "password": password},
            timeout=5  # 5 second timeout
        )
        
        if response.status_code == 200:
            # Login successful - extract JWT token
            data = response.json()
            token = data.get('token')
            
            # IMPORTANT: Redirect to PROFESSOR home page (not student home)
            resp = make_response(redirect(url_for('hp_professor.home_professor_page')))
            
            # Store JWT token in secure HTTP-only cookie
            resp.set_cookie('jwt_token', token, httponly=True, secure=False, samesite='Lax', max_age=86400)
            return resp
        else:
            # Invalid credentials
            flash("Invalid username or password")
            return render_template('loginPF.html')
            
    except Exception as e:
        # API call failed (server down, network error, etc.)
        flash("Login service unavailable. Please try again.")
        return render_template('loginPF.html')
