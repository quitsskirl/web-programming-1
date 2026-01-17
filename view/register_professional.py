# =============================================================================
# PROFESSIONAL REGISTRATION ROUTE - register_professional.py
# =============================================================================
# Handles professional/counselor account registration.
#
# URL: /register-professional
# TEMPLATE: registrationPF.html
#
# REGISTRATION FLOW:
# 1. User visits /register-professional (GET) -> sees registration form
# 2. User fills form and submits (POST)
# 3. Form data is sent to /api/register/professional endpoint
# 4. If successful: redirect to login page
# 5. If failed: show error message
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, flash

# Create Blueprint
register_pf_bp = Blueprint('register_pf', __name__)


# =============================================================================
# CONSTANTS
# =============================================================================
MIN_PASSWORD_LENGTH = 4

# Available specialties for professionals
SPECIALTIES = [
    "General Counselor",
    "Mental Health Counselor",
    "Academic Advisor",
    "Psychologist",
    "Career Counselor",
]

# Success/Error messages
MSG_SUCCESS = "Professional registered! Now log in."
MSG_FILL_ALL = "Please fill all required fields."
MSG_PASSWORD_SHORT = f"Password must be at least {MIN_PASSWORD_LENGTH} characters."


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def validate_registration(name, email, password, specialty):
    """
    Validate professional registration form data.
    
    Args:
        name: Professional's name
        email: Professional's email
        password: Professional's password
        specialty: Professional's specialty area
    
    Returns:
        tuple: (is_valid, error_message)
    """
    if not name or not email or not password or not specialty:
        return False, MSG_FILL_ALL
    if len(password) < MIN_PASSWORD_LENGTH:
        return False, MSG_PASSWORD_SHORT
    return True, None


# =============================================================================
# ROUTE HANDLERS
# =============================================================================
@register_pf_bp.route('/register-professional', methods=['GET', 'POST'])
def register_professional_page():
    """
    Display and process professional registration form.
    
    URL: http://localhost:5000/register-professional
    
    GET: Display the registration form
    POST: Process registration (handled by JavaScript calling API)
    
    The form submission is typically handled by JavaScript in the template,
    which calls the /api/register/professional endpoint directly.
    
    Form Data Expected:
        - name: Professional's display name
        - username: Professional's username/ID
        - password: Professional's password
        - specialty: Area of expertise
    
    Returns:
        Rendered registrationPF.html template with specialties list
    """
    if request.method == 'POST':
        # Get form data
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        specialty = request.form.get('specialty', '').strip()
        
        # Validate input
        is_valid, error_msg = validate_registration(name, email, password, specialty)
        if not is_valid:
            flash(error_msg)
            return render_template('registrationPF.html', specialties=SPECIALTIES)
        
        # TODO: Save to database via API call
        # For now, just redirect to login
        flash(MSG_SUCCESS)
        return redirect(url_for('login_pf.login_professional_page'))
    
    # GET request - show registration form
    return render_template('registrationPF.html', specialties=SPECIALTIES)
