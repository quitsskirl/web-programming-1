from flask import Blueprint, render_template

first_bp = Blueprint('first', __name__)

@first_bp.route('/')
def first_page():
    return render_template('FirstPage.html')
