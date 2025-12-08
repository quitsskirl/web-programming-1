from flask import Blueprint, render_template

# Create a Blueprint named 'info'
# Used in templates as: url_for('info.more_info_page')
info_bp = Blueprint('info', __name__)


@info_bp.route('/more-info')
def more_info_page():
    """
    Display the More Information page.
    
    URL: http://localhost:5000/more-info
    
    This informational page explains:
    - What psychological help is available
    - Who the wellbeing staff are
    - How the support system works
    
    Accessed from the Home page via the "More Info" button.
    Has a "Back" button to return to the home page.
    
    Returns:
        Rendered MoreInfo.html template
    """
    return render_template('MoreInfo.html')
