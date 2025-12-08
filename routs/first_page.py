from flask import Blueprint, render_template

# Create a Blueprint named 'first'
# - 'first' is the internal name used for url_for('first.first_page')
# - __name__ tells Flask where to find templates/static files
first_bp = Blueprint('first', __name__)


@first_bp.route('/')
def first_page():
    """
    Landing page route.
    
    URL: http://localhost:5000/
    
    This is the entry point of the application.
    Users choose their role (Student or Teacher) and are
    redirected to the appropriate registration page.
    
    Returns:
        Rendered FirstPage.html template
    """
    return render_template('FirstPage.html')
