from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
import requests

login_pf_bp = Blueprint('login_pf', __name__)

@login_pf_bp.route('/login-professional')
def login_professional_page():
    return render_template('loginPF.html')


@login_pf_bp.route('/login-professional', methods=['POST'])
def login_professional_post():
    username = request.form.get("username")
    password = request.form.get("password")

    # Call the JWT login API
    try:
        response = requests.post(
            request.url_root + 'api/login/professional',
            json={"username": username, "password": password},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            
            # Create response with redirect to professor home page
            resp = make_response(redirect(url_for('hp_professor.home_professor_page')))
            # Store token in cookie (httponly for security)
            resp.set_cookie('jwt_token', token, httponly=True, secure=False, samesite='Lax', max_age=86400)
            return resp
        else:
            flash("Invalid username or password")
            return render_template('loginPF.html')
    except Exception as e:
        # Fallback for when API is unavailable
        flash("Login service unavailable. Please try again.")
        return render_template('loginPF.html')
