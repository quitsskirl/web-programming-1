# =============================================================================
# EVENTS API ROUTES - routes/events_routes.py
# =============================================================================
# API endpoints for event image management (homepage slider).
#
# Endpoints:
#   GET /api/events/images - Get all event images
#   POST /api/events/upload-image - Upload event image
#   DELETE /api/events/images/<id> - Delete event image
#   PUT /api/events/images/<id>/order - Update image order
# =============================================================================

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from bson import ObjectId
import datetime
import os

import db  # Import module to get live references after init_db()
from auth.jwt_utils import token_required
from config import allowed_image

events_bp = Blueprint("events_api", __name__)


# =============================================================================
# GET ALL EVENT IMAGES
# =============================================================================
@events_bp.route("/api/events/images", methods=["GET"])
def get_event_images():
    """Get all event images for homepage slider (public)."""
    if db.event_images is None:
        return jsonify({"message": "Database unavailable"}), 503

    images = []
    for img in db.event_images.find().sort("order", 1):
        img["_id"] = str(img["_id"])
        img["created_at"] = str(img.get("created_at", ""))
        images.append(img)

    return jsonify(images), 200


# =============================================================================
# UPLOAD EVENT IMAGE
# =============================================================================
@events_bp.route("/api/events/upload-image", methods=["POST"])
@token_required
def upload_event_image():
    """Upload an event image (professionals only)."""
    if db.event_images is None:
        return jsonify({"message": "Database unavailable"}), 503

    if request.current_user.get('role') != 'professional':
        return jsonify({"message": "Only professionals can upload event images"}), 403

    if 'file' not in request.files:
        return jsonify({"message": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400

    if not allowed_image(file.filename):
        return jsonify({"message": "Only image files are allowed"}), 400

    filename = secure_filename(file.filename)
    unique_filename = f"{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
    
    events_folder = current_app.config.get('EVENT_IMAGES_FOLDER', 'static/uploads/events')
    filepath = os.path.join(events_folder, unique_filename)

    try:
        file.save(filepath)
    except Exception as e:
        return jsonify({"message": f"Failed to save file: {str(e)}"}), 500

    event_doc = {
        "title": request.form.get('title', 'Event'),
        "description": request.form.get('description', ''),
        "filename": unique_filename,
        "filepath": f"/static/uploads/events/{unique_filename}",
        "uploaded_by": request.current_user.get('username'),
        "created_at": datetime.datetime.utcnow(),
        "order": db.event_images.count_documents({})
    }

    result = db.event_images.insert_one(event_doc)

    return jsonify({
        "message": "Event image uploaded successfully!",
        "image_id": str(result.inserted_id),
        "filepath": event_doc["filepath"]
    }), 201


# =============================================================================
# DELETE EVENT IMAGE
# =============================================================================
@events_bp.route("/api/events/images/<image_id>", methods=["DELETE"])
@token_required
def delete_event_image(image_id):
    """Delete an event image (professionals only)."""
    if db.event_images is None:
        return jsonify({"message": "Database unavailable"}), 503

    if request.current_user.get('role') != 'professional':
        return jsonify({"message": "Only professionals can delete event images"}), 403

    try:
        image = db.event_images.find_one({"_id": ObjectId(image_id)})
    except:
        return jsonify({"message": "Invalid image ID"}), 400

    if not image:
        return jsonify({"message": "Image not found"}), 404

    # Delete file
    if image.get("filename"):
        events_folder = current_app.config.get('EVENT_IMAGES_FOLDER', 'static/uploads/events')
        filepath = os.path.join(events_folder, image["filename"])
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

    result = db.event_images.delete_one({"_id": ObjectId(image_id)})

    if result.deleted_count > 0:
        return jsonify({"message": "Event image deleted successfully!"}), 200
    return jsonify({"message": "Failed to delete image"}), 500


# =============================================================================
# UPDATE IMAGE ORDER
# =============================================================================
@events_bp.route("/api/events/images/<image_id>/order", methods=["PUT"])
@token_required
def update_event_image_order(image_id):
    """Update event image display order (professionals only)."""
    if db.event_images is None:
        return jsonify({"message": "Database unavailable"}), 503

    if request.current_user.get('role') != 'professional':
        return jsonify({"message": "Only professionals can reorder images"}), 403

    data = request.get_json(silent=True) or {}
    new_order = data.get('order')

    if new_order is None:
        return jsonify({"message": "Order value is required"}), 400

    try:
        result = db.event_images.update_one(
            {"_id": ObjectId(image_id)},
            {"$set": {"order": int(new_order)}}
        )

        if result.modified_count > 0:
            return jsonify({"message": "Order updated successfully!"}), 200
        return jsonify({"message": "No changes made"}), 200
    except:
        return jsonify({"message": "Invalid image ID"}), 400
