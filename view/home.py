# =============================================================================
# HOME PAGE ROUTE - home.py
# =============================================================================
# Student's main dashboard after logging in.
#
# URL: /home
# TEMPLATE: HomePage.html
# =============================================================================

from flask import Blueprint, render_template, session, redirect, url_for

# Create Blueprint
home_bp = Blueprint('home', __name__)


# =============================================================================
# ROUTE HANDLERS
# =============================================================================
@home_bp.route('/home', methods=['GET'])
def home_page():
    """
    Student's home page route.
    
    URL: http://localhost:5000/home
    
    This is where students land after logging in.
    The page displays:
    - Navigation menu (hamburger icon)
    - User info popup (username, tags)
    - Events carousel
    - Links to Services, Settings, More Info
    - Emergency contact button
    
    Returns:
        Rendered HomePage.html template
    """
    # Get user from session (if using session-based auth)
    user = session.get('user')
    return render_template('HomePage.html', user=user)


@home_bp.route('/logout', methods=['GET'])
def logout():
    """
    Logout route - clears session and redirects to first page.
    
    URL: http://localhost:5000/logout
    
    Returns:
        Redirect to landing page
    """
    session.clear()
    return redirect(url_for('first.first_page'))
