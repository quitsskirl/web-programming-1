from flask import Blueprint, render_template, request, redirect, url_for, flash

login_pf_bp = Blueprint('login_pf', __name__)

@login_pf_bp.route('/login-professional')
def login_professional_page():
    return render_template('loginPF.html')


@login_pf_bp.route('/login-professional', methods=['POST'])
def login_professional_post():
    username = request.form.get("username")
    password = request.form.get("password")

    # TEMPORARY EXAMPLE CREDENTIALS
    if username == "professor" and password == "123":
        return redirect(url_for('home.home_professor_page'))

    flash("Invalid username or password")
    return render_template('loginPF.html')
