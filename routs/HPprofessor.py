from flask import Blueprint, render_template

# Blueprint for professor-specific pages
hp_professor_bp = Blueprint('hp_professor', __name__)

@hp_professor_bp.route('/home-professor')
def home_professor_page():
    """Professor's home page - separate from student home page"""
    return render_template('HPprofessor.html')

