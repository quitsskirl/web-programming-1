from flask import Blueprint, render_template

# Create a Blueprint named 'hp_professor'
# Used in templates as: url_for('hp_professor.home_professor_page')
hp_professor_bp = Blueprint('hp_professor', __name__)


@hp_professor_bp.route('/home-professor')
def home_professor_page():
    """
    Professor's home page route.
    
    URL: http://localhost:5000/home-professor
    
    This is where professors land after logging in.
    The page displays:
    - Navigation menu with professor-specific links
    - User info popup
    - Professor dashboard content
    
    IMPORTANT: The menu links in this page point back to
    /home-professor (not /home) so professors stay in their area.
    
    Returns:
        Rendered HPprofessor.html template
    """
    return render_template('HPprofessor.html')
