from flask import Blueprint, render_template

# Create a Blueprint named 'register_st'
# Used in templates as: url_for('register_st.register_student_page')
register_st_bp = Blueprint('register_st', __name__)


@register_st_bp.route('/register-student')
def register_student_page():
    """
    Display student registration form.
    
    URL: http://localhost:5000/register-student
    
    Renders the registration form where students can:
    - Enter a username (student ID)
    - Create a password
    - Select characteristics/tags that describe them
    
    The form submission is handled by JavaScript in the template,
    which calls the /register API endpoint.
    
    Returns:
        Rendered registerST.html template
    """
    return render_template('registerST.html')
