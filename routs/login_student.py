from flask import Blueprint, render_template

login_st_bp = Blueprint('login_st', __name__)

@login_st_bp.route('/login-student')
def login_student_page():
    return render_template('loginST.html')
