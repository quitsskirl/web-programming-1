from flask import Blueprint, render_template

register_pf_bp = Blueprint('register_pf', __name__)

@register_pf_bp.route('/register-professional')
def register_professional_page():
    return render_template('registrationPF.html')
