# =============================================================================
# SETTINGS PAGE ROUTE - settings.py
# =============================================================================
# Account settings for students and professors.
#
# URL: /settings (students), /settings-professor (professors)
# TEMPLATES: Settings.html, SettingsProfessor.html
# =============================================================================

from flask import Blueprint, render_template, request, session, redirect, url_for, flash

# Create Blueprint
settings_bp = Blueprint('settings', __name__)


# =============================================================================
# CONSTANTS
# =============================================================================
DEFAULT_THEME = 'light'
AVAILABLE_THEMES = ['light', 'dark', 'nature']


# =============================================================================
# ROUTE HANDLERS
# =============================================================================
@settings_bp.route('/settings', methods=['GET', 'POST'])
def settings_page():
    """
    Display the Settings page for STUDENTS.
    
    URL: http://localhost:5000/settings
    
    GET: Display settings form
    POST: Save settings and redirect
    
    This page allows students to:
    - View their account information
    - Change their password
    - Manage notification preferences
    - Delete their account
    - Log out
    
    Returns:
        Rendered Settings.html template
    """
    if request.method == 'POST':
        # Example settings update (theme preference)
        theme = request.form.get('theme', DEFAULT_THEME)
        if theme in AVAILABLE_THEMES:
            session['theme'] = theme
            flash('Settings saved!')
        return redirect(url_for('settings.settings_page'))
    
    # GET request - show settings form
    current_theme = session.get('theme', DEFAULT_THEME)
    return render_template('Settings.html', theme=current_theme)


@settings_bp.route('/settings-professor', methods=['GET', 'POST'])
def settings_professor_page():
    """
    Display the Settings page for PROFESSORS.
    
    URL: http://localhost:5000/settings-professor
    
    GET: Display settings form
    POST: Save settings and redirect
    
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
    if request.method == 'POST':
        # Example settings update
        theme = request.form.get('theme', DEFAULT_THEME)
        if theme in AVAILABLE_THEMES:
            session['theme'] = theme
            flash('Settings saved!')
        return redirect(url_for('settings.settings_professor_page'))
    
    current_theme = session.get('theme', DEFAULT_THEME)
    return render_template('SettingsProfessor.html', theme=current_theme)
