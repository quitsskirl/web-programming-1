# =============================================================================
# STUDENT REGISTRATION ROUTE - register_student.py
# =============================================================================
# Handles student account registration.
#
# URL: /register-student
# TEMPLATE: registerST.html
#
# REGISTRATION FLOW:
# 1. User visits /register-student (GET) -> sees registration form
# 2. User fills form and submits (POST)
# 3. Form data is sent to /register API endpoint
# 4. If successful: redirect to login page
# 5. If failed: show error message
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash

# Create Blueprint
register_st_bp = Blueprint('register_st', __name__)


# =============================================================================
# CONSTANTS
# =============================================================================
MIN_PASSWORD_LENGTH = 4

# Success/Error messages
MSG_SUCCESS = "Student registered! Now log in."
MSG_FILL_ALL = "Please fill all required fields."
MSG_PASSWORD_SHORT = f"Password must be at least {MIN_PASSWORD_LENGTH} characters."


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def validate_registration(name, email, password):
    """
    Validate registration form data.
    
    Args:
        name: Student's name
        email: Student's email
        password: Student's password
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not name or not email or not password:
        return False, MSG_FILL_ALL
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, MSG_PASSWORD_SHORT
    return True, None


# =============================================================================
# ROUTE HANDLERS
# =============================================================================
@register_st_bp.route('/register-student', methods=['GET', 'POST'])
def register_student_page():
    """
    Display and process student registration form.
    
    URL: http://localhost:5000/register-student
    
    GET: Display the registration form
    POST: Process registration (handled by JavaScript calling /register API)
    
    The form submission is typically handled by JavaScript in the template,
    which calls the /register API endpoint directly.
    
    Form Data Expected:
        - name: Student's display name
        - username: Student's username/ID
        - password: Student's password
        - tags: Optional characteristics/interests
    
    Returns:
        Rendered registerST.html template
    """
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        # Validate input
        is_valid, error_msg = validate_registration(name, email, password)
        if not is_valid:
            flash(error_msg)
            return render_template('registerST.html')
        
        # TODO: Save to database via API call
        # For now, just redirect to login
        flash(MSG_SUCCESS)
        return redirect(url_for('login_st.login_student_page'))
    
    # GET request - show registration form
    return render_template('registerST.html')
