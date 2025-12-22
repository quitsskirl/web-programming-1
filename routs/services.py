from flask import Blueprint, render_template

# Create a Blueprint named 'services'
# Used in templates as: url_for('services.services_page')
services_bp = Blueprint('services', __name__)


@services_bp.route('/services')
def services_page():
    """
    Display the Services/Counseling page.
    
    URL: http://localhost:5000/services
    
    This page shows all registered professionals that students
    can connect with for mental health support.
    
    Loads professionals from the database dynamically.
    
    Returns:
        Rendered Services.html template with professionals list
    """
    # Import here to avoid circular imports
    from app import professionals
    
    # Get all professionals from database
    professionals_list = []
    if professionals is not None:
        for pro in professionals.find():
            professionals_list.append({
                "username": pro.get("username", ""),
                "specialty": pro.get("specialty", "General Counselor"),
                "bio": pro.get("bio", "Available for support sessions.")
            })
    
    return render_template('Services.html', professionals=professionals_list)
