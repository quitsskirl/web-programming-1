from flask import Blueprint, render_template

# Create a Blueprint named 'register_pf'
# Used in templates as: url_for('register_pf.register_professional_page')
register_pf_bp = Blueprint('register_pf', __name__)


@register_pf_bp.route('/register-professional')
def register_professional_page():
    """
    Display professor registration form.
    
    URL: http://localhost:5000/register-professional
    
    Renders the registration form where professors can:
    - Enter a username (professor ID)
    - Create a password
    
    The form submission is handled by JavaScript in the template,
    which currently saves to localStorage.
    
    Returns:
        Rendered registrationPF.html template
    """
    return render_template('registrationPF.html')
