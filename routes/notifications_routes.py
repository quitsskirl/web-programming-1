# =============================================================================
# NOTIFICATIONS API ROUTES - routes/notifications_routes.py
# =============================================================================
# API endpoints for user notifications.
#
# Endpoints:
#   GET /api/notifications - Get user's notifications
#   PUT /api/notifications/<id>/read - Mark notification as read
# =============================================================================

from flask import Blueprint, request, jsonify
from bson import ObjectId
import datetime

import db  # Import module to get live references after init_db()
from auth.jwt_utils import token_required

notifications_bp = Blueprint("notifications_api", __name__)


# =============================================================================
# GET NOTIFICATIONS
# =============================================================================
@notifications_bp.route("/api/notifications", methods=["GET"])
@token_required
def get_notifications():
    """Get all notifications for the current user."""
    if db.notifications is None:
        return jsonify({"message": "Database unavailable"}), 503

    username = request.current_user.get('username')

    user_notifications = []
    for n in db.notifications.find({"user_id": username}).sort("created_at", -1):
        n["_id"] = str(n["_id"])
        n["created_at"] = str(n.get("created_at", ""))
        user_notifications.append(n)

    return jsonify(user_notifications), 200


# =============================================================================
# MARK NOTIFICATION AS READ
# =============================================================================
@notifications_bp.route("/api/notifications/<notification_id>/read", methods=["PUT"])
@token_required
def mark_notification_read(notification_id):
    """Mark a notification as read."""
    if db.notifications is None:
        return jsonify({"message": "Database unavailable"}), 503

    try:
        result = db.notifications.update_one(
            {"_id": ObjectId(notification_id)},
            {"$set": {"read": True}}
        )

        if result.modified_count > 0:
            return jsonify({"message": "Notification marked as read"}), 200
        return jsonify({"message": "Notification not found"}), 404
    except:
        return jsonify({"message": "Invalid notification ID"}), 400


# =============================================================================
# HELPER FUNCTION: CREATE NOTIFICATION
# =============================================================================
def create_notification(user_id, title, message, notif_type="general"):
    """
    Helper function to create notifications.
    Called internally when events happen.
    
    Args:
        user_id: Username to notify
        title: Notification title
        message: Notification message
        notif_type: Type (general, appointment, reminder, message)
    
    Returns:
        Insert result or None
    """
    if db.notifications is None:
        return None

    notif = {
        "notification_id": f"notif_{datetime.datetime.utcnow().timestamp()}",
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": notif_type,
        "read": False,
        "created_at": datetime.datetime.utcnow()
    }

    return db.notifications.insert_one(notif)
