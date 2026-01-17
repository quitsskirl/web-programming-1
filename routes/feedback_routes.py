# =============================================================================
# FEEDBACK API ROUTES - routes/feedback_routes.py
# =============================================================================
# API endpoints for user feedback collection.
#
# Endpoints:
#   GET /api/feedback/status - Check if user should see feedback popup
#   POST /api/feedback/track-activity - Track user activity
#   POST /api/feedback/submit - Submit feedback
#   POST /api/feedback/dismiss - Dismiss feedback popup
#   GET /api/feedback/all - Get all feedback (professionals only)
# =============================================================================

from flask import Blueprint, request, jsonify
import datetime

import db  # Import module to get live references after init_db()
from auth.jwt_utils import token_required

feedback_bp = Blueprint("feedback_api", __name__)


# =============================================================================
# CHECK FEEDBACK STATUS
# =============================================================================
@feedback_bp.route("/api/feedback/status", methods=["GET"])
@token_required
def check_feedback_status():
    """Check if user should see feedback popup."""
    if db.students is None and db.professionals is None:
        return jsonify({"message": "Database unavailable"}), 503

    username = request.current_user.get('username')
    role = request.current_user.get('role')

    if role == 'student':
        user = db.students.find_one({"username": username}) if db.students else None
    else:
        user = db.professionals.find_one({"username": username}) if db.professionals else None

    if not user:
        return jsonify({"message": "User not found"}), 404

    has_given_feedback = user.get('has_given_feedback', False)
    activity_count = user.get('activity_count', 0)
    should_show_feedback = not has_given_feedback and activity_count >= 3

    return jsonify({
        "has_given_feedback": has_given_feedback,
        "activity_count": activity_count,
        "should_show_feedback": should_show_feedback
    }), 200


# =============================================================================
# TRACK USER ACTIVITY
# =============================================================================
@feedback_bp.route("/api/feedback/track-activity", methods=["POST"])
@token_required
def track_activity():
    """Increment user's activity count."""
    if db.students is None and db.professionals is None:
        return jsonify({"message": "Database unavailable"}), 503

    username = request.current_user.get('username')
    role = request.current_user.get('role')

    if role == 'student':
        collection = db.students if db.students is not None else None
    else:
        collection = db.professionals if db.professionals is not None else None

    if collection is None:
        return jsonify({"message": "Database unavailable"}), 503

    result = collection.update_one(
        {"username": username},
        {"$inc": {"activity_count": 1}}
    )

    if result.modified_count > 0:
        return jsonify({"message": "Activity tracked"}), 200
    return jsonify({"message": "User not found"}), 404


# =============================================================================
# SUBMIT FEEDBACK
# =============================================================================
@feedback_bp.route("/api/feedback/submit", methods=["POST"])
@token_required
def submit_feedback():
    """Submit user feedback."""
    if db.feedback is None:
        return jsonify({"message": "Database unavailable"}), 503

    username = request.current_user.get('username')
    role = request.current_user.get('role')

    data = request.get_json(silent=True) or {}
    rating = data.get('rating')
    comment = data.get('comment', '').strip()

    if not rating or not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({"message": "Rating must be between 1 and 5"}), 400

    feedback_doc = {
        "username": username,
        "role": role,
        "rating": rating,
        "comment": comment,
        "created_at": datetime.datetime.utcnow()
    }

    db.feedback.insert_one(feedback_doc)

    # Mark user as having given feedback
    if role == 'student' and db.students is not None:
        db.students.update_one(
            {"username": username},
            {"$set": {"has_given_feedback": True}}
        )
    elif role == 'professional' and db.professionals is not None:
        db.professionals.update_one(
            {"username": username},
            {"$set": {"has_given_feedback": True}}
        )

    return jsonify({
        "message": "Thank you for your feedback!",
        "rating": rating
    }), 201


# =============================================================================
# DISMISS FEEDBACK
# =============================================================================
@feedback_bp.route("/api/feedback/dismiss", methods=["POST"])
@token_required
def dismiss_feedback():
    """Dismiss feedback popup temporarily."""
    return jsonify({"message": "Feedback dismissed temporarily"}), 200


# =============================================================================
# GET ALL FEEDBACK (Professionals only)
# =============================================================================
@feedback_bp.route("/api/feedback/all", methods=["GET"])
@token_required
def get_all_feedback():
    """Get all feedback entries (professionals only)."""
    if db.feedback is None:
        return jsonify({"message": "Database unavailable"}), 503

    if request.current_user.get('role') != 'professional':
        return jsonify({"message": "Access denied"}), 403

    all_feedback = []
    for fb in db.feedback.find().sort("created_at", -1):
        fb["_id"] = str(fb["_id"])
        fb["created_at"] = str(fb.get("created_at", ""))
        all_feedback.append(fb)

    return jsonify(all_feedback), 200
