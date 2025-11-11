from flask import Blueprint, render_template

register_st_bp = Blueprint('register_st', __name__)

@register_st_bp.route('/register-student')
def register_student_page():
    return render_template('registerST.html')
