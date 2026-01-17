# =============================================================================
# FIRST PAGE ROUTE - first_page.py
# =============================================================================
# This is the landing page of the application.
# Users choose their role (Student or Teacher) here.
#
# URL: /
# TEMPLATE: FirstPage.html
# =============================================================================

from flask import Blueprint, render_template, redirect, url_for

# Create Blueprint
first_bp = Blueprint('first', __name__)


# =============================================================================
# CONSTANTS
# =============================================================================
PAGE_TITLE = "Welcome to Mental Health Support"


# =============================================================================
# ROUTE HANDLERS
# =============================================================================
@first_bp.route('/', methods=['GET'])
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


@first_bp.route('/start', methods=['GET'])
def start():
    """
    Redirect to home page.
    
    URL: http://localhost:5000/start
    
    Alternative entry point that redirects to the student home page.
    
    Returns:
        Redirect to home page
    """
    return redirect(url_for('home.home_page'))
