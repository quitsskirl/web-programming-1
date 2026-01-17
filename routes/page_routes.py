# =============================================================================
# PAGE ROUTES - routes/page_routes.py
# =============================================================================
# All HTML page routes (render templates).
# These are the pages users actually see.
# =============================================================================

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, make_response, jsonify, current_app
from functools import wraps
import requests
import jwt

# Create Blueprint for all page routes
pages_bp = Blueprint('pages', __name__)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_current_user():
    """Get current user from JWT token in cookies."""
    token = request.cookies.get('jwt_token')
    if not token:
        return None
    try:
        secret = current_app.config.get('JWT_SECRET_KEY', 'your-secret-key')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except:
        return None


def login_required(f):
    """Decorator requiring authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('pages.login_student_page'))
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


def student_required(f):
    """Decorator requiring student role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('pages.login_student_page'))
        if user.get('role') != 'student':
            return jsonify({"message": "Access denied"}), 403
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


def professional_required(f):
    """Decorator requiring professional role."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('pages.login_professional_page'))
        if user.get('role') != 'professional':
            return jsonify({"message": "Access denied"}), 403
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


# =============================================================================
# CONSTANTS
# =============================================================================
API_TIMEOUT = 5
COOKIE_MAX_AGE = 86400


# =============================================================================
# LANDING PAGE
# =============================================================================
@pages_bp.route('/', methods=['GET'])
def first_page():
    """Landing page - users choose their role here."""
    return render_template('FirstPage.html')


@pages_bp.route('/start', methods=['GET'])
def start():
    """Redirect to home page."""
    return redirect(url_for('pages.home_page'))


# =============================================================================
# HOME PAGES
# =============================================================================
@pages_bp.route('/home', methods=['GET'])
def home_page():
    """Student home page."""
    user = session.get('user')
    return render_template('HomePage.html', user=user)


@pages_bp.route('/home-professor', methods=['GET'])
def home_professor_page():
    """Professor home page."""
    user = session.get('user')
    return render_template('HPprofessor.html', user=user)


@pages_bp.route('/logout', methods=['GET'])
def logout():
    """Logout - clear session and cookies."""
    session.clear()
    resp = make_response(redirect(url_for('pages.first_page')))
    resp.set_cookie('jwt_token', '', expires=0)
    return resp


# =============================================================================
# LOGIN PAGES
# =============================================================================
@pages_bp.route('/login-student', methods=['GET', 'POST'])
def login_student_page():
    """Student login page."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter username and password')
            return render_template('loginST.html')
        
        try:
            response = requests.post(
                request.url_root + 'api/login/student',
                json={"username": username, "password": password},
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                session['user'] = {'role': 'student', 'username': username}
                
                resp = make_response(redirect(url_for('pages.home_page')))
                resp.set_cookie('jwt_token', token, httponly=True, secure=False, 
                              samesite='Lax', max_age=COOKIE_MAX_AGE)
                return resp
            else:
                flash('Invalid username or password')
                return render_template('loginST.html')
        except:
            flash('Login service unavailable')
            return render_template('loginST.html')
    
    return render_template('loginST.html')


@pages_bp.route('/login-professional', methods=['GET', 'POST'])
def login_professional_page():
    """Professional login page."""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Please enter username and password')
            return render_template('loginPF.html')
        
        try:
            response = requests.post(
                request.url_root + 'api/login/professional',
                json={"username": username, "password": password},
                timeout=API_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                session['user'] = {'role': 'professional', 'username': username}
                
                resp = make_response(redirect(url_for('pages.home_professor_page')))
                resp.set_cookie('jwt_token', token, httponly=True, secure=False,
                              samesite='Lax', max_age=COOKIE_MAX_AGE)
                return resp
            else:
                flash('Invalid username or password')
                return render_template('loginPF.html')
        except:
            flash('Login service unavailable')
            return render_template('loginPF.html')
    
    return render_template('loginPF.html')


# =============================================================================
# REGISTRATION PAGES
# =============================================================================
@pages_bp.route('/register-student', methods=['GET'])
def register_student_page():
    """Student registration page."""
    return render_template('registerST.html')


@pages_bp.route('/register-professional', methods=['GET'])
def register_professional_page():
    """Professional registration page."""
    return render_template('registrationPF.html')


# =============================================================================
# INFO & SERVICE PAGES
# =============================================================================
@pages_bp.route('/more-info', methods=['GET'])
def more_info_page():
    """More information page."""
    return render_template('MoreInfo.html')


@pages_bp.route('/services', methods=['GET'])
def services_page():
    """Services page - shows available professionals."""
    import db
    
    professionals_list = []
    if db.professionals is not None:
        for pro in db.professionals.find():
            professionals_list.append({
                "username": pro.get("username", ""),
                "specialty": pro.get("specialty", "General Counselor"),
                "bio": pro.get("bio", "Available for support sessions.")
            })
    
    return render_template('Services.html', professionals=professionals_list)


# =============================================================================
# SETTINGS PAGES
# =============================================================================
@pages_bp.route('/settings', methods=['GET', 'POST'])
def settings_page():
    """Student settings page."""
    return render_template('Settings.html')


@pages_bp.route('/settings-professor', methods=['GET', 'POST'])
def settings_professor_page():
    """Professor settings page."""
    return render_template('SettingsProfessor.html')


# =============================================================================
# RESOURCES PAGES
# =============================================================================
@pages_bp.route('/resources', methods=['GET'])
@login_required
def resources_page():
    """Student resources page."""
    return render_template('Resources.html')


@pages_bp.route('/resources-professor', methods=['GET'])
@professional_required
def resources_professor_page():
    """Professor resources management page."""
    return render_template('ResourcesProfessor.html')


# =============================================================================
# SUPPORT CLASSIFIER PAGE
# =============================================================================
@pages_bp.route('/support-classifier', methods=['GET'])
def support_classifier_page():
    """AI support classifier page."""
    return render_template('SupportClassifier.html')


# =============================================================================
# APPOINTMENT PAGES
# =============================================================================
@pages_bp.route('/book-appointment', methods=['GET', 'POST'])
@student_required
def book_appointment():
    """Book appointment page for students."""
    import db
    from routes.notifications_routes import create_notification
    from datetime import datetime
    
    if request.method == 'POST':
        if db.appointments is None:
            return jsonify({"message": "Database unavailable"}), 503
        
        professional_id = request.form.get('professional')
        date = request.form.get('date')
        time = request.form.get('time')
        reason = request.form.get('reason', '')
        student_username = request.current_user.get('username')
        
        appointment = {
            "student_username": student_username,
            "professional_username": professional_id,
            "date": date,
            "time": time,
            "reason": reason,
            "status": "scheduled",
            "created_at": datetime.utcnow()
        }
        
        db.appointments.insert_one(appointment)
        
        create_notification(
            user_id=professional_id,
            title="New Appointment Request",
            message=f"Student {student_username} booked on {date} at {time}.",
            notif_type="appointment"
        )
        
        return redirect(url_for('pages.booking_success'))
    
    professionals_list = []
    if db.professionals is not None:
        for pro in db.professionals.find():
            professionals_list.append({
                "username": pro.get("username", ""),
                "specialty": pro.get("specialty", "General Counselor")
            })
    
    return render_template('BookAppointment.html', professionals=professionals_list)


@pages_bp.route('/booking-success')
@student_required
def booking_success():
    """Booking confirmation page."""
    return render_template('BookingSuccess.html')


@pages_bp.route('/my-appointments')
@professional_required
def my_appointments():
    """Professional's appointments page."""
    import db
    
    professional_username = request.current_user.get('username')
    
    appointments_list = []
    if db.appointments is not None:
        for apt in db.appointments.find({"professional_username": professional_username}).sort("date", -1):
            if apt.get("_schema"):
                continue
            apt["_id"] = str(apt["_id"])
            apt["created_at"] = str(apt.get("created_at", ""))
            appointments_list.append(apt)
    
    return render_template('MyAppointments.html', appointments=appointments_list)


@pages_bp.route('/student-appointments')
@student_required
def student_appointments():
    """Student's appointments page."""
    import db
    
    student_username = request.current_user.get('username')
    
    appointments_list = []
    if db.appointments is not None:
        for apt in db.appointments.find({"student_username": student_username}).sort("date", -1):
            if apt.get("_schema"):
                continue
            apt["_id"] = str(apt["_id"])
            apt["created_at"] = str(apt.get("created_at", ""))
            appointments_list.append(apt)
    
    return render_template('StudentAppointments.html', appointments=appointments_list)


@pages_bp.route('/update-appointment-status', methods=['POST'])
@professional_required
def update_appointment_status():
    """Update appointment status."""
    import db
    from bson import ObjectId
    
    if db.appointments is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    appointment_id = request.form.get('appointment_id')
    new_status = request.form.get('status')
    professional_username = request.current_user.get('username')
    
    result = db.appointments.update_one(
        {"_id": ObjectId(appointment_id), "professional_username": professional_username},
        {"$set": {"status": new_status}}
    )
    
    if result.modified_count > 0:
        return redirect(url_for('pages.my_appointments'))
    return jsonify({"message": "Not found"}), 404
