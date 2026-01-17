# =============================================================================
# PROFESSOR HOME PAGE ROUTE - HPprofessor.py
# =============================================================================
# Professor's main dashboard after logging in.
#
# URL: /home-professor
# TEMPLATE: HPprofessor.html
#
# NOTE: Python file names should usually be lowercase (like h_professor.py),
# but we keep this name for consistency with existing code.
# =============================================================================

from flask import Blueprint, render_template, session, redirect, url_for

# Create Blueprint
hp_professor_bp = Blueprint('hp_professor', __name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_user_from_session():
    """
    Get current user from session.
    
    Returns:
        dict: User info or None if not logged in
    """
    return session.get('user')


def is_professional(user):
    """
    Check if user has professional role.
    
    Args:
        user: User dictionary from session
    
    Returns:
        bool: True if user is a professional
    """
    if not user:
        return False
    return user.get('role') == 'professional'


# =============================================================================
# ROUTE HANDLERS
# =============================================================================
@hp_professor_bp.route('/home-professor', methods=['GET'])
def home_professor_page():
    """
    Professor's home page route.
    
    URL: http://localhost:5000/home-professor
    
    This is where professors land after logging in.
    The page displays:
    - Navigation menu with professor-specific links
    - User info popup
    - Professor dashboard content
    - Links to appointments, resources, settings
    
    IMPORTANT: The menu links in this page point back to
    /home-professor (not /home) so professors stay in their area.
    
    Access Control:
        Only users with role='professional' should access this page.
        Others are redirected to the professional login page.
    
    Returns:
        Rendered HPprofessor.html template
    """
    # Optional: Check if user is logged in as professional
    user = get_user_from_session()
    
    # If you want to enforce authentication, uncomment below:
    # if not is_professional(user):
    #     return redirect(url_for('login_pf.login_professional_page'))
    
    return render_template('HPprofessor.html', user=user)


@hp_professor_bp.route('/professor/dashboard', methods=['GET'])
def dashboard():
    """
    Alternative dashboard route for professors.
    
    URL: http://localhost:5000/professor/dashboard
    
    Same as home_professor_page but with different URL structure.
    Useful if you want /professor/* URL pattern.
    
    Returns:
        Rendered HPprofessor.html template or redirect to login
    """
    user = get_user_from_session()
    
    if not is_professional(user):
        return redirect(url_for('login_pf.login_professional_page'))
    
    return render_template('HPprofessor.html', user=user)
