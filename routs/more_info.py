from flask import Blueprint, render_template

info_bp = Blueprint('info', __name__)

@info_bp.route('/more-info')
def more_info_page():
    return render_template('MoreInfo.html')
