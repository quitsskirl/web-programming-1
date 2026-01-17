# =============================================================================
# RESOURCES PAGE ROUTE - resources.py
# =============================================================================
# Mental health resources for students and management for professors.
#
# URL: /resources (students), /resources-professor (professors)
# TEMPLATES: Resources.html, ResourcesProfessor.html
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for
import jwt
import os

# Create Blueprint
resources_bp = Blueprint('resources', __name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_current_user():
    """
    Helper to get current user from JWT token in cookies.
    
    Returns:
        dict: User payload from JWT token, or None if not authenticated
    """
    token = request.cookies.get('jwt_token')
    if not token:
        return None
    try:
        secret = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except:
        return None


def filter_resources(items, query):
    """
    Filter resources by search query.
    
    Args:
        items: List of resource dictionaries
        query: Search query string
    
    Returns:
        Filtered list of resources
    """
    if not query:
        return items
    q = query.strip().lower()
    return [x for x in items if q in x.get('title', '').lower()]


# =============================================================================
# ROUTE HANDLERS
# =============================================================================
@resources_bp.route('/resources', methods=['GET'])
def resources_page():
    """
    Display the Resources page for students.
    
    URL: http://localhost:5000/resources
    
    This page provides mental health resources including:
    - Articles and guides
    - PDF documents
    - Helpful links
    - Videos and tutorials
    
    Query Parameters:
        q: Optional search query to filter resources
    
    Returns:
        Rendered Resources.html template
    """
    # Check if user is logged in
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login_st.login_student_page'))
    
    # Get search query from URL parameters
    q = request.args.get('q', '').strip()
    
    return render_template('Resources.html', q=q)


@resources_bp.route('/resources-professor', methods=['GET'])
def resources_professor_page():
    """
    Display the Resources management page for professors.
    
    URL: http://localhost:5000/resources-professor
    
    This page allows professors to:
    - Upload PDF resources
    - Add video resources
    - Delete existing resources
    - View all uploaded resources
    
    Returns:
        Rendered ResourcesProfessor.html template
    """
    # Check if user is logged in and is a professional
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login_pf.login_professional_page'))
    
    if current_user.get('role') != 'professional':
        return redirect(url_for('login_pf.login_professional_page'))
    
    return render_template('ResourcesProfessor.html')
