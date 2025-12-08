from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
import requests  # Used to call our own API internally

# Create a Blueprint named 'login_st'
# Used in templates as: url_for('login_st.login_student_page')
login_st_bp = Blueprint('login_st', __name__)


@login_st_bp.route('/login-student')
def login_student_page():
    """
    Display student login form (GET request).
    
    URL: http://localhost:5000/login-student
    
    Simply renders the login form. The actual authentication
    happens when the form is submitted (POST request).
    
    Returns:
        Rendered loginST.html template
    """
    return render_template('loginST.html')


@login_st_bp.route('/login-student', methods=['POST'])
def login_student_post():
    """
    Process student login (POST request).
    
    URL: http://localhost:5000/login-student (POST)
    
    This function:
    1. Gets username/password from the submitted form
    2. Calls our JWT API to verify credentials
    3. If valid: stores token in cookie, redirects to home
    4. If invalid: shows error message, stays on login page
    
    Form Data Expected:
        - username: Student's username
        - password: Student's password
    
    Returns:
        - Success: Redirect to /home with JWT cookie set
        - Failure: Re-render login page with error message
    """
    # Get form data
    username = request.form.get("username")
    password = request.form.get("password")

    # Call our JWT login API
    try:
        # Make internal API call to verify credentials
        response = requests.post(
            request.url_root + 'api/login/student',  # http://localhost:5000/api/login/student
            json={"username": username, "password": password},
            timeout=5  # 5 second timeout
        )
        
        if response.status_code == 200:
            # Login successful - extract JWT token
            data = response.json()
            token = data.get('token')
            
            # Create redirect response to student home page
            resp = make_response(redirect(url_for('home.home_page')))
            
            # Store JWT token in secure HTTP-only cookie
            # - httponly=True: JavaScript cannot access this cookie (XSS protection)
            # - secure=False: Allow HTTP (set True in production with HTTPS)
            # - samesite='Lax': Prevents CSRF attacks
            # - max_age=86400: Cookie expires in 24 hours (matches JWT expiration)
            resp.set_cookie('jwt_token', token, httponly=True, secure=False, samesite='Lax', max_age=86400)
            return resp
        else:
            # Invalid credentials
            flash("Invalid username or password")
            return render_template('loginST.html')
            
    except Exception as e:
        # API call failed (server down, network error, etc.)
        flash("Login service unavailable. Please try again.")
        return render_template('loginST.html')
