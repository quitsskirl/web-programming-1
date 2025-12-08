from flask import Blueprint, render_template

# Create a Blueprint named 'settings'
# Used in templates as: url_for('settings.settings_page')
settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings')
def settings_page():
    """
    Display the Settings page.
    
    URL: http://localhost:5000/settings
    
    This page allows users to:
    - View their account information
    - Change their password
    - Manage notification preferences
    - Delete their account
    - Log out
    
    The page uses JavaScript (Settings.js) to:
    - Load user info from localStorage
    - Toggle visibility of settings forms
    - Handle form submissions
    
    Returns:
        Rendered Settings.html template
    """
    return render_template('Settings.html')
