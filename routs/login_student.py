from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
import requests

login_st_bp = Blueprint('login_st', __name__)

@login_st_bp.route('/login-student')
def login_student_page():
    return render_template('loginST.html')


@login_st_bp.route('/login-student', methods=['POST'])
def login_student_post():
    username = request.form.get("username")
    password = request.form.get("password")

    # Call the JWT login API
    try:
        response = requests.post(
            request.url_root + 'api/login/student',
            json={"username": username, "password": password},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('token')
            
            # Create response with redirect
            resp = make_response(redirect(url_for('home.home_page')))
            # Store token in cookie (httponly for security)
            resp.set_cookie('jwt_token', token, httponly=True, secure=False, samesite='Lax', max_age=86400)
            return resp
        else:
            flash("Invalid username or password")
            return render_template('loginST.html')
    except Exception as e:
        flash("Login service unavailable. Please try again.")
        return render_template('loginST.html')
