# =============================================================================
# SERVICES PAGE ROUTE - services.py
# =============================================================================
# Displays all available counseling services and professionals.
#
# URL: /services
# TEMPLATE: Services.html
# =============================================================================

from flask import Blueprint, render_template

# Create Blueprint
services_bp = Blueprint('services', __name__)


# =============================================================================
# SAMPLE DATA (used when database is unavailable)
# =============================================================================
SAMPLE_SERVICES = [
    {"name": "Counseling", "desc": "Talk to a professional"},
    {"name": "Academic Support", "desc": "Help with study planning"},
    {"name": "Crisis Support", "desc": "Immediate help for emergencies"},
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_professionals_from_db():
    """
    Get all professionals from database.
    
    Returns:
        list: List of professional dictionaries with username, specialty, bio
    """
    # Import from new structure
    from db import professionals
    
    professionals_list = []
    if professionals is not None:
        for pro in professionals.find():
            professionals_list.append({
                "username": pro.get("username", ""),
                "specialty": pro.get("specialty", "General Counselor"),
                "bio": pro.get("bio", "Available for support sessions.")
            })
    return professionals_list


# =============================================================================
# ROUTE HANDLERS
# =============================================================================
@services_bp.route('/services', methods=['GET'])
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
    professionals_list = get_professionals_from_db()
    
    return render_template(
        'Services.html', 
        professionals=professionals_list,
        services=SAMPLE_SERVICES
    )
