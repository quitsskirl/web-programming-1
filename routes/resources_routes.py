# =============================================================================
# RESOURCES API ROUTES - routes/resources_routes.py
# =============================================================================
# API endpoints for resource management (PDFs, videos).
#
# Endpoints:
#   GET /api/resources - Get all resources
#   POST /api/resources - Add resource
#   GET /api/resources/pdfs - Get PDF resources
#   GET /api/resources/videos - Get video resources
#   POST /api/resources/upload-pdf - Upload PDF
#   POST /api/resources/add-video - Add video
#   PUT /api/resources/<id> - Update resource
#   DELETE /api/resources/<id> - Delete resource
# =============================================================================

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from bson import ObjectId
import datetime
import os

import db  # Import module to get live references after init_db()
from auth.jwt_utils import token_required
from config import allowed_pdf

resources_bp = Blueprint("resources_api", __name__)


# =============================================================================
# GET ALL RESOURCES
# =============================================================================
@resources_bp.route("/api/resources", methods=["GET"])
def get_resources():
    """Get all resources (public)."""
    if db.resources is None:
        return jsonify({"message": "Database unavailable"}), 503

    all_resources = []
    for r in db.resources.find():
        r["_id"] = str(r["_id"])
        all_resources.append(r)

    return jsonify(all_resources), 200


# =============================================================================
# ADD RESOURCE
# =============================================================================
@resources_bp.route("/api/resources", methods=["POST"])
@token_required
def add_resource():
    """Add a new resource (professionals only)."""
    if db.resources is None:
        return jsonify({"message": "Database unavailable"}), 503

    if request.current_user.get('role') != 'professional':
        return jsonify({"message": "Only professionals can add resources"}), 403

    data = request.get_json(silent=True) or {}

    resource = {
        "title": data.get("title"),
        "content": data.get("content"),
        "category": data.get("category", "general"),
        "added_by": request.current_user.get('username'),
        "created_at": datetime.datetime.utcnow()
    }

    db.resources.insert_one(resource)
    return jsonify({"message": "Resource added successfully!"}), 201


# =============================================================================
# GET PDF RESOURCES
# =============================================================================
@resources_bp.route("/api/resources/pdfs", methods=["GET"])
def get_pdf_resources():
    """Get all PDF resources (public)."""
    if db.resources is None:
        return jsonify({"message": "Database unavailable"}), 503

    pdf_resources = []
    for r in db.resources.find({"resource_type": "pdf"}).sort("created_at", -1):
        r["_id"] = str(r["_id"])
        r["created_at"] = str(r.get("created_at", ""))
        pdf_resources.append(r)

    return jsonify(pdf_resources), 200


# =============================================================================
# GET VIDEO RESOURCES
# =============================================================================
@resources_bp.route("/api/resources/videos", methods=["GET"])
def get_video_resources():
    """Get all video resources (public)."""
    if db.resources is None:
        return jsonify({"message": "Database unavailable"}), 503

    video_resources = []
    for r in db.resources.find({"resource_type": "video"}).sort("created_at", -1):
        r["_id"] = str(r["_id"])
        r["created_at"] = str(r.get("created_at", ""))
        video_resources.append(r)

    return jsonify(video_resources), 200


# =============================================================================
# UPLOAD PDF
# =============================================================================
@resources_bp.route("/api/resources/upload-pdf", methods=["POST"])
@token_required
def upload_pdf_resource():
    """Upload a PDF resource (professionals only)."""
    if db.resources is None:
        return jsonify({"message": "Database unavailable"}), 503

    if request.current_user.get('role') != 'professional':
        return jsonify({"message": "Only professionals can upload resources"}), 403

    if 'file' not in request.files:
        return jsonify({"message": "No file provided"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400

    if not allowed_pdf(file.filename):
        return jsonify({"message": "Only PDF files are allowed"}), 400

    filename = secure_filename(file.filename)
    unique_filename = f"{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
    
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads/pdfs')
    filepath = os.path.join(upload_folder, unique_filename)

    try:
        file.save(filepath)
    except Exception as e:
        return jsonify({"message": f"Failed to save file: {str(e)}"}), 500

    resource_doc = {
        "title": request.form.get('title', filename.replace('.pdf', '')),
        "description": request.form.get('description', ''),
        "category": request.form.get('category', 'article'),
        "resource_type": "pdf",
        "filename": unique_filename,
        "filepath": f"/static/uploads/pdfs/{unique_filename}",
        "original_filename": filename,
        "uploaded_by": request.current_user.get('username'),
        "created_at": datetime.datetime.utcnow()
    }

    result = db.resources.insert_one(resource_doc)

    return jsonify({
        "message": "PDF uploaded successfully!",
        "resource_id": str(result.inserted_id),
        "filepath": resource_doc["filepath"]
    }), 201


# =============================================================================
# ADD VIDEO
# =============================================================================
@resources_bp.route("/api/resources/add-video", methods=["POST"])
@token_required
def add_video_resource():
    """Add a video resource by URL (professionals only)."""
    if db.resources is None:
        return jsonify({"message": "Database unavailable"}), 503

    if request.current_user.get('role') != 'professional':
        return jsonify({"message": "Only professionals can add resources"}), 403

    data = request.get_json(silent=True) or {}
    title = data.get('title', '').strip()
    video_url = data.get('video_url', '').strip()
    description = data.get('description', '').strip()

    if not title or not video_url:
        return jsonify({"message": "Title and video URL are required"}), 400

    video_doc = {
        "title": title,
        "description": description,
        "video_url": video_url,
        "resource_type": "video",
        "uploaded_by": request.current_user.get('username'),
        "created_at": datetime.datetime.utcnow()
    }

    result = db.resources.insert_one(video_doc)

    return jsonify({
        "message": "Video added successfully!",
        "resource_id": str(result.inserted_id)
    }), 201


# =============================================================================
# UPDATE RESOURCE
# =============================================================================
@resources_bp.route("/api/resources/<resource_id>", methods=["PUT"])
@token_required
def update_resource(resource_id):
    """Update a resource (professionals only)."""
    if db.resources is None:
        return jsonify({"message": "Database unavailable"}), 503

    if request.current_user.get('role') != 'professional':
        return jsonify({"message": "Only professionals can edit resources"}), 403

    try:
        resource = db.resources.find_one({"_id": ObjectId(resource_id)})
    except:
        return jsonify({"message": "Invalid resource ID"}), 400

    if not resource:
        return jsonify({"message": "Resource not found"}), 404

    data = request.get_json(silent=True) or {}
    update_fields = {}

    if "title" in data and data["title"].strip():
        update_fields["title"] = data["title"].strip()
    if "description" in data:
        update_fields["description"] = data["description"].strip()
    if "video_url" in data and data["video_url"].strip():
        update_fields["video_url"] = data["video_url"].strip()

    if not update_fields:
        return jsonify({"message": "No fields to update"}), 400

    result = db.resources.update_one(
        {"_id": ObjectId(resource_id)},
        {"$set": update_fields}
    )

    if result.modified_count > 0:
        return jsonify({"message": "Resource updated successfully!"}), 200
    return jsonify({"message": "No changes made"}), 200


# =============================================================================
# DELETE RESOURCE
# =============================================================================
@resources_bp.route("/api/resources/<resource_id>", methods=["DELETE"])
@token_required
def delete_resource(resource_id):
    """Delete a resource (professionals only)."""
    if db.resources is None:
        return jsonify({"message": "Database unavailable"}), 503

    if request.current_user.get('role') != 'professional':
        return jsonify({"message": "Only professionals can delete resources"}), 403

    try:
        resource = db.resources.find_one({"_id": ObjectId(resource_id)})
    except:
        return jsonify({"message": "Invalid resource ID"}), 400

    if not resource:
        return jsonify({"message": "Resource not found"}), 404

    # Delete file if PDF
    if resource.get("resource_type") == "pdf" and resource.get("filename"):
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads/pdfs')
        filepath = os.path.join(upload_folder, resource["filename"])
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

    result = db.resources.delete_one({"_id": ObjectId(resource_id)})

    if result.deleted_count > 0:
        return jsonify({"message": "Resource deleted successfully!"}), 200
    return jsonify({"message": "Failed to delete resource"}), 500
