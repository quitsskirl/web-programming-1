from flask import Blueprint, render_template

# Create a Blueprint named 'settings'
# Used in templates as: url_for('settings.settings_page')
settings_bp = Blueprint('settings', __name__)


@settings_bp.route('/settings')
def settings_page():
    """
    Display the Settings page for STUDENTS.
    
    URL: http://localhost:5000/settings
    
    This page allows students to:
    - View their account information
    - Change their password
    - Manage notification preferences
    - Delete their account
    - Log out
    
    Returns:
        Rendered Settings.html template
    """
    return render_template('Settings.html')


@settings_bp.route('/settings-professor')
def settings_professor_page():
    """
    Display the Settings page for PROFESSORS.
    
    URL: http://localhost:5000/settings-professor
    
    This page allows professors to:
    - View their account information and specialty
    - Change their password
    - Manage notification preferences
    - Update availability
    - Delete their account
    - Log out
    
    Returns:
        Rendered SettingsProfessor.html template
    """
    return render_template('SettingsProfessor.html')
