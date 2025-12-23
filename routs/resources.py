from flask import Blueprint, render_template, request, redirect, url_for
import jwt
import os

# Create a Blueprint named 'resources'
# Used in templates as: url_for('resources.resources_page')
resources_bp = Blueprint('resources', __name__)


def get_current_user():
    """Helper to get current user from JWT token in cookies"""
    token = request.cookies.get('jwt_token')
    if not token:
        return None
    try:
        secret = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except:
        return None


@resources_bp.route('/resources')
def resources_page():
    """
    Display the Resources page for students.
    
    URL: http://localhost:5000/resources
    
    This page provides mental health resources including:
    - Articles and guides
    - PDF documents
    - Helpful links
    - Videos and tutorials
    
    Returns:
        Rendered Resources.html template
    """
    # Check if user is logged in
    current_user = get_current_user()
    if not current_user:
        return redirect(url_for('login_st.login_student_page'))
    
    return render_template('Resources.html')


@resources_bp.route('/resources-professor')
def resources_professor_page():
    """
    Display the Resources management page for professors.
    
    URL: http://localhost:5000/resources-professor
    
    This page allows professors to:
    - Upload PDF resources
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

