from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from datetime import datetime
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create Blueprint for appointments
appointments_bp = Blueprint('appointments', __name__)


@appointments_bp.route('/book-appointment', methods=['GET', 'POST'])
def book_appointment():
    """
    Book an appointment with a professional.
    FOR STUDENTS ONLY.
    
    URL: http://localhost:5000/book-appointment
    
    GET: Display the booking form with list of professionals
    POST: Create a new appointment in the database
    
    Returns:
        GET: Rendered BookAppointment.html template
        POST: Redirect to student home page with success message
    """
    # Import here to avoid circular imports
    from app import professionals, appointments
    
    if request.method == 'POST':
        # Check if database is available
        if appointments is None:
            return jsonify({"message": "Database unavailable"}), 503
        
        # Get form data
        professional_id = request.form.get('professional')
        date = request.form.get('date')
        time = request.form.get('time')
        reason = request.form.get('reason', '')
        
        # Get username from localStorage (sent via hidden field)
        student_username = request.form.get('student_username', 'Guest')
        
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
def booking_success():
    """
    Show booking confirmation for students.
    
    URL: http://localhost:5000/booking-success
    """
    return render_template('BookingSuccess.html')


@appointments_bp.route('/my-appointments')
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
    
    # Get professional username from query param (sent by JS from localStorage)
    professional_username = request.args.get('professional', None)
    
    # Get all appointments for this professional
    appointments_list = []
    if appointments is not None:
        query = {}
        if professional_username:
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
def update_appointment_status():
    """
    Update appointment status (confirm, complete, cancel).
    FOR PROFESSIONALS ONLY.
    
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
    
    # Update the appointment status
    result = appointments.update_one(
        {"_id": ObjectId(appointment_id)},
        {"$set": {"status": new_status}}
    )
    
    if result.modified_count > 0:
        return redirect(url_for('appointments.my_appointments'))
    else:
        return jsonify({"message": "Appointment not found"}), 404


@appointments_bp.route('/student-appointments')
def student_appointments():
    """
    View appointments for students - shows their booked appointments.
    FOR STUDENTS ONLY.
    
    URL: http://localhost:5000/student-appointments
    """
    from app import appointments
    
    # Get student username from query param
    student_username = request.args.get('student', None)
    
    appointments_list = []
    if appointments is not None:
        query = {}
        if student_username:
            query = {"student_username": student_username}
        
        for apt in appointments.find(query).sort("date", -1):
            if apt.get("_schema"):
                continue
            apt["_id"] = str(apt["_id"])
            apt["created_at"] = str(apt.get("created_at", ""))
            appointments_list.append(apt)
    
    return render_template('StudentAppointments.html', appointments=appointments_list)
