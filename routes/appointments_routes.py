# =============================================================================
# APPOINTMENTS API ROUTES - routes/appointments_routes.py
# =============================================================================
# API endpoints for appointment management.
#
# Endpoints:
#   POST /api/appointments - Create appointment
#   GET /api/appointments - Get user's appointments
# =============================================================================

from flask import Blueprint, request, jsonify
import datetime

import db  # Import module to get live references after init_db()
from auth.jwt_utils import token_required

appointments_bp = Blueprint("appointments_api", __name__)


# =============================================================================
# CREATE APPOINTMENT
# =============================================================================
@appointments_bp.route("/api/appointments", methods=["POST"])
@token_required
def create_appointment():
    """Create a new appointment."""
    if db.appointments is None:
        return jsonify({"message": "Database unavailable"}), 503

    current_user = request.current_user
    data = request.get_json(silent=True) or {}

    appointment = {
        "student_username": current_user.get('username'),
        "professional_username": data.get("professional"),
        "date": data.get("date"),
        "time": data.get("time"),
        "reason": data.get("reason", ""),
        "status": "pending",
        "created_at": datetime.datetime.utcnow()
    }

    result = db.appointments.insert_one(appointment)

    return jsonify({
        "message": "Appointment requested!",
        "appointment_id": str(result.inserted_id)
    }), 201


# =============================================================================
# GET APPOINTMENTS
# =============================================================================
@appointments_bp.route("/api/appointments", methods=["GET"])
@token_required
def get_appointments():
    """Get appointments for the logged-in user."""
    if db.appointments is None:
        return jsonify({"message": "Database unavailable"}), 503

    current_user = request.current_user
    username = current_user.get('username')
    role = current_user.get('role')

    # Filter based on role
    if role == 'student':
        query = {"student_username": username}
    else:
        query = {"professional_username": username}

    user_appointments = []
    for apt in db.appointments.find(query):
        apt["_id"] = str(apt["_id"])
        apt["created_at"] = str(apt.get("created_at", ""))
        user_appointments.append(apt)

    return jsonify(user_appointments), 200
