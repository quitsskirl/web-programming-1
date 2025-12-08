from flask import Blueprint, render_template

# Create a Blueprint named 'services'
# Used in templates as: url_for('services.services_page')
services_bp = Blueprint('services', __name__)


@services_bp.route('/services')
def services_page():
    """
    Display the Services/Counseling page.
    
    URL: http://localhost:5000/services
    
    This page shows available counselors that students
    can chat with for mental health support.
    
    Currently displays placeholder counselor cards.
    In the future, this would load actual counselors
    from the database with their availability status.
    
    Returns:
        Rendered Services.html template
    """
    return render_template('Services.html')
