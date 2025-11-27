from flask import Blueprint, render_template

home_bp = Blueprint('home', __name__)

@home_bp.route('/home')
def home_page():
    return render_template('HomePage.html')
@home_bp.route('/home-professor')
def home_professor_page():
    return render_template('HPprofessor.html')
