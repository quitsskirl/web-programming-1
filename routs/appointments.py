from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime
from functools import wraps
import os
import sys
import jwt

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create Blueprint for appointments
appointments_bp = Blueprint('appointments', __name__)


def get_current_user():
    """
    Helper function to get current user from JWT token.
    Checks both cookies and Authorization header.
    Returns user payload dict or None if not authenticated.
    """
    from flask import current_app
    
    token = None
    
    # Check cookie first (for page routes)
    token = request.cookies.get('jwt_token')
    
    # Fallback to Authorization header (for API routes)
    if not token and 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
    
    # Fallback to query parameter
    if not token:
        token = request.args.get('token')
    
    if not token:
        return None
    
    try:
        secret_key = current_app.config.get('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return payload
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None


def login_required_page(f):
    """
    Decorator for page routes that require authentication.
    Redirects to login page if not authenticated.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            # Redirect to login page
            return redirect(url_for('login_st.login_student_page'))
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


def professional_required(f):
    """
    Decorator for routes that require professional role.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('login_pf.login_professional_page'))
        if user.get('role') != 'professional':
            return jsonify({"message": "Access denied. Professionals only."}), 403
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


def student_required(f):
    """
    Decorator for routes that require student role.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return redirect(url_for('login_st.login_student_page'))
        if user.get('role') != 'student':
            return jsonify({"message": "Access denied. Students only."}), 403
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


@appointments_bp.route('/book-appointment', methods=['GET', 'POST'])
@student_required  # Bug 1 Fix: Require student authentication
def book_appointment():
    """
    Book an appointment with a professional.
    FOR STUDENTS ONLY - requires authentication.
    
    URL: http://localhost:5000/book-appointment
    
    GET: Display the booking form with list of professionals
    POST: Create a new appointment in the database
    
    Returns:
        GET: Rendered BookAppointment.html template
        POST: Redirect to student home page with success message
    """
    # Import here to avoid circular imports
    from app import professionals, appointments, create_notification
    
    if request.method == 'POST':
        # Check if database is available
        if appointments is None:
            return jsonify({"message": "Database unavailable"}), 503
        
        # Get form data
        professional_id = request.form.get('professional')
        date = request.form.get('date')
        time = request.form.get('time')
        reason = request.form.get('reason', '')
        
        # Bug 1 Fix: Use authenticated user's username instead of form field
        # This prevents users from booking appointments for other students
        student_username = request.current_user.get('username')
        
        # Create appointment document
        appointment = {
            "student_username": student_username,
            "professional_username": professional_id,
            "date": date,
            "time": time,
            "reason": reason,
            "status": "scheduled",
            "created_at": datetime.utcnow()
        }
        
        # Insert into database
        appointments.insert_one(appointment)
        
        # Create notification for the professional
        create_notification(
            user_id=professional_id,
            title="New Appointment Request",
            message=f"Student {student_username} has booked an appointment with you on {date} at {time}.",
            notif_type="appointment"
        )
        
        # Redirect to student booking confirmation page
        return redirect(url_for('appointments.booking_success'))
    
    # GET request - show the booking form
    professionals_list = []
    if professionals is not None:
        for pro in professionals.find():
            professionals_list.append({
                "username": pro.get("username", ""),
                "specialty": pro.get("specialty", "General Counselor")
            })
    
    return render_template('BookAppointment.html', professionals=professionals_list)


@appointments_bp.route('/booking-success')
@student_required  # Require authentication for success page too
def booking_success():
    """
    Show booking confirmation for students.
    
    URL: http://localhost:5000/booking-success
    """
    return render_template('BookingSuccess.html')


@appointments_bp.route('/my-appointments')
@professional_required  # Bug 1 Fix: Require professional authentication
def my_appointments():
    """
    View all appointments for professionals.
    FOR PROFESSIONALS ONLY - shows appointments booked with them.
    
    URL: http://localhost:5000/my-appointments
    
    Returns:
        Rendered MyAppointments.html template with appointments list
    """
    # Import here to avoid circular imports
    from app import appointments
    
    # Bug 2 Fix: Use authenticated user's username from JWT token
    # Don't rely on query parameters which can be manipulated
    professional_username = request.current_user.get('username')
    
    # Get all appointments for this professional only
    appointments_list = []
    if appointments is not None and professional_username:
        # Bug 2 Fix: Always filter by the authenticated user
        query = {"professional_username": professional_username}
        
        for apt in appointments.find(query).sort("date", -1):
            # Skip schema documents
            if apt.get("_schema"):
                continue
            apt["_id"] = str(apt["_id"])
            apt["created_at"] = str(apt.get("created_at", ""))
            appointments_list.append(apt)
    
    return render_template('MyAppointments.html', appointments=appointments_list)


@appointments_bp.route('/update-appointment-status', methods=['POST'])
@professional_required  # Bug 1 Fix: Require professional authentication
def update_appointment_status():
    """
    Update appointment status (confirm, complete, cancel).
    FOR PROFESSIONALS ONLY - requires authentication.
    
    URL: http://localhost:5000/update-appointment-status
    """
    from app import appointments
    from bson import ObjectId
    
    if appointments is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    appointment_id = request.form.get('appointment_id')
    new_status = request.form.get('status')
    
    if not appointment_id or not new_status:
        return jsonify({"message": "Missing appointment_id or status"}), 400
    
    # Bug 1 Fix: Verify the appointment belongs to this professional before updating
    professional_username = request.current_user.get('username')
    
    # Update the appointment status only if it belongs to this professional
    result = appointments.update_one(
        {
            "_id": ObjectId(appointment_id),
            "professional_username": professional_username  # Security: verify ownership
        },
        {"$set": {"status": new_status}}
    )
    
    if result.modified_count > 0:
        return redirect(url_for('appointments.my_appointments'))
    else:
        return jsonify({"message": "Appointment not found or access denied"}), 404


@appointments_bp.route('/student-appointments')
@student_required  # Bug 1 Fix: Require student authentication
def student_appointments():
    """
    View appointments for students - shows their booked appointments.
    FOR STUDENTS ONLY - requires authentication.
    
    URL: http://localhost:5000/student-appointments
    """
    from app import appointments
    
    # Bug 2 Fix: Use authenticated user's username from JWT token
    # Don't rely on query parameters which can be manipulated
    student_username = request.current_user.get('username')
    
    appointments_list = []
    if appointments is not None and student_username:
        # Bug 2 Fix: Always filter by the authenticated user
        query = {"student_username": student_username}
        
        for apt in appointments.find(query).sort("date", -1):
            if apt.get("_schema"):
                continue
            apt["_id"] = str(apt["_id"])
            apt["created_at"] = str(apt.get("created_at", ""))
            appointments_list.append(apt)
    
    return render_template('StudentAppointments.html', appointments=appointments_list)
