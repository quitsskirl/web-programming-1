# =============================================================================
# AUTHENTICATION API ROUTES - routes/auth_routes.py
# =============================================================================
# API endpoints for user authentication and account management.
#
# Endpoints:
#   POST /register - Register student
#   POST /api/login/student - Student login
#   POST /api/login/professional - Professional login
#   POST /api/register/professional - Register professional
#   GET /api/verify-token - Verify JWT token
#   PUT /api/student/update - Update student profile
#   PUT /api/professional/update - Update professional profile
#   PUT /api/student/change-password - Change student password
#   PUT /api/professional/change-password - Change professional password
#   DELETE /api/student/delete - Delete student account
#   DELETE /api/professional/delete - Delete professional account
#   GET /students - Get all students (debug)
# =============================================================================

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

from config import HASH_METHOD, SALT_LENGTH
import db  # Import module to get live references after init_db()
from auth.jwt_utils import generate_token, token_required
import os

auth_bp = Blueprint("auth", __name__)


# =============================================================================
# STUDENT REGISTRATION
# =============================================================================
@auth_bp.route("/register", methods=["POST"])
def register_student():
    """Register a new student account."""
    if db.students is None:
        return jsonify({"message": "Database unavailable"}), 503

    data = request.get_json(silent=True) or request.form.to_dict()
    username = data.get("username")
    password = data.get("password")
    tags = data.get("tags", [])

    if not isinstance(tags, list):
        tags = [tags]

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    if db.students.find_one({"username": username}):
        return jsonify({"message": "Username already exists"}), 400

    hashed_pw = generate_password_hash(password, method=HASH_METHOD, salt_length=SALT_LENGTH)
    db.students.insert_one({"username": username, "password": hashed_pw, "tags": tags})

    return jsonify({"message": "Student registered successfully!"}), 201


# =============================================================================
# STUDENT LOGIN
# =============================================================================
@auth_bp.route("/api/login/student", methods=["POST"])
def login_student():
    """Authenticate student and return JWT token."""
    if db.students is None:
        return jsonify({"message": "Database unavailable"}), 503

    data = request.get_json(silent=True) or request.form.to_dict()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    user = db.students.find_one({"username": username})
    if not user or not check_password_hash(user.get("password", ""), password):
        return jsonify({"message": "Invalid username or password"}), 401

    token = generate_token(user["_id"], username, role="student")

    tags = user.get("tags", [])
    tags_str = ", ".join(tags) if isinstance(tags, list) else str(tags)

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "username": username,
            "role": "student",
            "tags": tags_str,
            "email": user.get("email", ""),
            "bio": user.get("bio", "")
        }
    }), 200


# =============================================================================
# PROFESSIONAL LOGIN
# =============================================================================
@auth_bp.route("/api/login/professional", methods=["POST"])
def login_professional():
    """Authenticate professional and return JWT token."""
    if db.professionals is None:
        return jsonify({"message": "Database unavailable"}), 503

    data = request.get_json(silent=True) or request.form.to_dict()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    user = db.professionals.find_one({"username": username})
    if not user or not check_password_hash(user.get("password", ""), password):
        return jsonify({"message": "Invalid username or password"}), 401

    token = generate_token(user["_id"], username, role="professional")

    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "username": username,
            "role": "professional",
            "specialty": user.get("specialty", ""),
            "email": user.get("email", ""),
            "bio": user.get("bio", ""),
            "availability": user.get("availability", "")
        }
    }), 200


# =============================================================================
# PROFESSIONAL REGISTRATION
# =============================================================================
@auth_bp.route("/api/register/professional", methods=["POST"])
def register_professional():
    """Register a new professional account."""
    if db.professionals is None:
        return jsonify({"message": "Database unavailable"}), 503

    data = request.get_json(silent=True) or request.form.to_dict()
    username = data.get("username")
    password = data.get("password")
    specialty = data.get("specialty", "")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    if db.professionals.find_one({"username": username}):
        return jsonify({"message": "Username already exists"}), 400

    hashed_pw = generate_password_hash(password, method=HASH_METHOD, salt_length=SALT_LENGTH)
    db.professionals.insert_one({
        "username": username,
        "password": hashed_pw,
        "specialty": specialty
    })

    return jsonify({"message": "Professional registered successfully!"}), 201


# =============================================================================
# TOKEN VERIFICATION
# =============================================================================
@auth_bp.route("/api/verify-token", methods=["GET"])
@token_required
def verify_token():
    """Verify if JWT token is still valid."""
    return jsonify({
        "valid": True,
        "user": request.current_user
    }), 200


# =============================================================================
# PROTECTED ROUTE EXAMPLE
# =============================================================================
@auth_bp.route("/api/protected", methods=["GET"])
@token_required
def protected_route():
    """Example protected route."""
    return jsonify({
        "message": f"Hello {request.current_user['username']}! You have access.",
        "role": request.current_user['role']
    }), 200


# =============================================================================
# UPDATE STUDENT PROFILE
# =============================================================================
@auth_bp.route("/api/student/update", methods=["PUT"])
@token_required
def update_student():
    """Update student profile (tags, email, bio)."""
    if db.students is None:
        return jsonify({"message": "Database unavailable"}), 503

    current_user = request.current_user
    username = current_user.get('username')

    if current_user.get('role') != 'student':
        return jsonify({"message": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    update_fields = {}

    if "tags" in data:
        tags = data["tags"]
        if not isinstance(tags, list):
            tags = [tags]
        update_fields["tags"] = tags

    if "email" in data:
        update_fields["email"] = data["email"]

    if "bio" in data:
        update_fields["bio"] = data["bio"]

    if not update_fields:
        return jsonify({"message": "No fields to update"}), 400

    result = db.students.update_one(
        {"username": username},
        {"$set": update_fields}
    )

    if result.modified_count > 0:
        return jsonify({"message": "Profile updated successfully!"}), 200
    return jsonify({"message": "No changes made"}), 200


# =============================================================================
# UPDATE PROFESSIONAL PROFILE
# =============================================================================
@auth_bp.route("/api/professional/update", methods=["PUT"])
@token_required
def update_professional():
    """Update professional profile."""
    if db.professionals is None:
        return jsonify({"message": "Database unavailable"}), 503

    current_user = request.current_user
    username = current_user.get('username')

    if current_user.get('role') != 'professional':
        return jsonify({"message": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    update_fields = {}

    if "specialty" in data:
        update_fields["specialty"] = data["specialty"]
    if "email" in data:
        update_fields["email"] = data["email"]
    if "bio" in data:
        update_fields["bio"] = data["bio"]
    if "availability" in data:
        update_fields["availability"] = data["availability"]

    if not update_fields:
        return jsonify({"message": "No fields to update"}), 400

    result = db.professionals.update_one(
        {"username": username},
        {"$set": update_fields}
    )

    if result.modified_count > 0:
        return jsonify({"message": "Profile updated successfully!"}), 200
    return jsonify({"message": "No changes made"}), 200


# =============================================================================
# CHANGE STUDENT PASSWORD
# =============================================================================
@auth_bp.route("/api/student/change-password", methods=["PUT"])
@token_required
def change_student_password():
    """Change student password."""
    if db.students is None:
        return jsonify({"message": "Database unavailable"}), 503

    current_user = request.current_user
    username = current_user.get('username')

    if current_user.get('role') != 'student':
        return jsonify({"message": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password", "").strip()
    new_password = data.get("new_password", "").strip()

    if not old_password or not new_password:
        return jsonify({"message": "Both passwords are required"}), 400

    if len(new_password) < 4:
        return jsonify({"message": "Password must be at least 4 characters"}), 400

    user = db.students.find_one({"username": username})
    if not user:
        return jsonify({"message": "User not found"}), 404

    if not check_password_hash(user.get("password", ""), old_password):
        return jsonify({"message": "Current password is incorrect"}), 401

    new_hashed = generate_password_hash(new_password, method=HASH_METHOD, salt_length=SALT_LENGTH)
    db.students.update_one({"username": username}, {"$set": {"password": new_hashed}})

    return jsonify({"message": "Password changed successfully!"}), 200


# =============================================================================
# CHANGE PROFESSIONAL PASSWORD
# =============================================================================
@auth_bp.route("/api/professional/change-password", methods=["PUT"])
@token_required
def change_professional_password():
    """Change professional password."""
    if db.professionals is None:
        return jsonify({"message": "Database unavailable"}), 503

    current_user = request.current_user
    username = current_user.get('username')

    if current_user.get('role') != 'professional':
        return jsonify({"message": "Access denied"}), 403

    data = request.get_json(silent=True) or {}
    old_password = data.get("old_password", "").strip()
    new_password = data.get("new_password", "").strip()

    if not old_password or not new_password:
        return jsonify({"message": "Both passwords are required"}), 400

    if len(new_password) < 4:
        return jsonify({"message": "Password must be at least 4 characters"}), 400

    user = db.professionals.find_one({"username": username})
    if not user:
        return jsonify({"message": "User not found"}), 404

    if not check_password_hash(user.get("password", ""), old_password):
        return jsonify({"message": "Current password is incorrect"}), 401

    new_hashed = generate_password_hash(new_password, method=HASH_METHOD, salt_length=SALT_LENGTH)
    db.professionals.update_one({"username": username}, {"$set": {"password": new_hashed}})

    return jsonify({"message": "Password changed successfully!"}), 200


# =============================================================================
# DELETE STUDENT ACCOUNT
# =============================================================================
@auth_bp.route("/api/student/delete", methods=["DELETE"])
@token_required
def delete_student():
    """Delete student account and all related data."""
    if db.students is None:
        return jsonify({"message": "Database unavailable"}), 503

    current_user = request.current_user
    username = current_user.get('username')

    if current_user.get('role') != 'student':
        return jsonify({"message": "Access denied"}), 403

    deleted_data = {"appointments": 0, "support_tickets": 0, "notifications": 0}

    if db.appointments is not None:
        result = db.appointments.delete_many({"student_username": username})
        deleted_data["appointments"] = result.deleted_count

    if db.support_tickets is not None:
        result = db.support_tickets.delete_many({
            "$or": [{"user_id": username}, {"sender_user_id": username}]
        })
        deleted_data["support_tickets"] = result.deleted_count

    if db.notifications is not None:
        result = db.notifications.delete_many({"user_id": username})
        deleted_data["notifications"] = result.deleted_count

    result = db.students.delete_one({"username": username})

    if result.deleted_count > 0:
        return jsonify({
            "message": "Account deleted successfully!",
            "deleted_data": deleted_data
        }), 200
    return jsonify({"message": "Account not found"}), 404


# =============================================================================
# DELETE PROFESSIONAL ACCOUNT
# =============================================================================
@auth_bp.route("/api/professional/delete", methods=["DELETE"])
@token_required
def delete_professional():
    """Delete professional account and all related data."""
    if db.professionals is None:
        return jsonify({"message": "Database unavailable"}), 503

    current_user = request.current_user
    username = current_user.get('username')

    if current_user.get('role') != 'professional':
        return jsonify({"message": "Access denied"}), 403

    deleted_data = {"appointments": 0, "resources": 0, "notifications": 0, "pdf_files": 0}

    if db.appointments is not None:
        result = db.appointments.delete_many({"professional_username": username})
        deleted_data["appointments"] = result.deleted_count

    if db.resources is not None:
        from flask import current_app
        pdf_list = list(db.resources.find({"uploaded_by": username, "resource_type": "pdf"}))
        for pdf in pdf_list:
            if pdf.get("filename"):
                filepath = os.path.join(current_app.config.get('UPLOAD_FOLDER', ''), pdf["filename"])
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        deleted_data["pdf_files"] += 1
                except Exception:
                    pass
        result = db.resources.delete_many({"uploaded_by": username})
        deleted_data["resources"] = result.deleted_count

    if db.notifications is not None:
        result = db.notifications.delete_many({"user_id": username})
        deleted_data["notifications"] = result.deleted_count

    result = db.professionals.delete_one({"username": username})

    if result.deleted_count > 0:
        return jsonify({
            "message": "Account deleted successfully!",
            "deleted_data": deleted_data
        }), 200
    return jsonify({"message": "Account not found"}), 404


# =============================================================================
# GET ALL STUDENTS (DEBUG)
# =============================================================================
@auth_bp.route("/students", methods=["GET"])
def get_students():
    """Get all students (debug endpoint)."""
    if db.students is None:
        return jsonify({"message": "Database unavailable"}), 503

    all_students = []
    for s in db.students.find():
        s["_id"] = str(s["_id"])
        all_students.append(s)

    return jsonify(all_students), 200
