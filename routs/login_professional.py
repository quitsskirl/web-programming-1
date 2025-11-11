from flask import Blueprint, render_template

login_pf_bp = Blueprint('login_pf', __name__)

@login_pf_bp.route('/login-professional')
def login_professional_page():
    return render_template('loginPF.html')
