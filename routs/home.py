from flask import Blueprint, render_template

# Create a Blueprint named 'home'
# Used in templates as: url_for('home.home_page')
home_bp = Blueprint('home', __name__)


@home_bp.route('/home')
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
    return render_template('HomePage.html')
