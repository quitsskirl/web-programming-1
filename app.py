from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash

# Password hashing configuration - uses scrypt with salt
# Format stored: scrypt:32768:8:1$<salt>$<hash>
HASH_METHOD = 'scrypt'
SALT_LENGTH = 16
from dotenv import load_dotenv
from functools import wraps
import os
import jwt
import datetime
from routs import all_blueprints

# Load Environment Variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')
app.config['JWT_EXPIRATION_HOURS'] = 24


# ===== JWT HELPER FUNCTIONS =====
def generate_token(user_id, username, role='student'):
    """Generate a JWT token for authenticated users"""
    payload = {
        'user_id': str(user_id),
        'username': username,
        'role': role,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=app.config['JWT_EXPIRATION_HOURS']),
        'iat': datetime.datetime.utcnow()
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')


def token_required(f):
    """Decorator to protect routes that require authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
        
        # Also check for token in query params (for convenience)
        if not token:
            token = request.args.get('token')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(*args, **kwargs)
    return decorated

# MongoDB Connection
mongo_uri = os.getenv("MONGO_URI")
client = None
db = None
students = None

professionals = None

if mongo_uri:
    try:
        client = MongoClient(
            mongo_uri,
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
        client.admin.command("ping")
        db = client["healthDB"]
        students = db["students"]
        professionals = db["professionals"]
        print("✅ MongoDB connection OK!")
    except Exception as e:
        print("❌ MongoDB connection failed:", e)
        client = None
        db = None
        students = None
        professionals = None
else:
    print("⚠️ MONGO_URI not set. Database features will be unavailable.")

# Register Blueprints
for bp in all_blueprints:
    app.register_blueprint(bp)

# ===== ROUTES =====
@app.route("/register", methods=["POST"])
def register_student():
    if students is None:
        return jsonify({"message": "Database unavailable"}), 503

    data = request.get_json(silent=True)
    if not data:
        data = request.form.to_dict()

    username = data.get("username")
    password = data.get("password")
    tags = data.get("tags", [])

    if not isinstance(tags, list):
        tags = [tags]

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    if students.find_one({"username": username}):
        return jsonify({"message": "Username already exists"}), 400

    hashed_pw = generate_password_hash(password, method=HASH_METHOD, salt_length=SALT_LENGTH)
    students.insert_one({"username": username, "password": hashed_pw, "tags": tags})

    return jsonify({"message": "Student registered successfully!"}), 201


@app.route("/api/login/student", methods=["POST"])
def login_student():
    """Login endpoint for students - returns JWT token"""
    if students is None:
        return jsonify({"message": "Database unavailable"}), 503

    data = request.get_json(silent=True)
    if not data:
        data = request.form.to_dict()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    user = students.find_one({"username": username})
    if not user:
        return jsonify({"message": "Invalid username or password"}), 401

    if not check_password_hash(user.get("password", ""), password):
        return jsonify({"message": "Invalid username or password"}), 401

    token = generate_token(user["_id"], username, role='student')
    
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "username": username,
            "role": "student"
        }
    }), 200


@app.route("/api/login/professional", methods=["POST"])
def login_professional():
    """Login endpoint for professionals - returns JWT token"""
    if professionals is None:
        return jsonify({"message": "Database unavailable"}), 503

    data = request.get_json(silent=True)
    if not data:
        data = request.form.to_dict()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    user = professionals.find_one({"username": username})
    if not user:
        return jsonify({"message": "Invalid username or password"}), 401

    if not check_password_hash(user.get("password", ""), password):
        return jsonify({"message": "Invalid username or password"}), 401

    token = generate_token(user["_id"], username, role='professional')
    
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "username": username,
            "role": "professional"
        }
    }), 200


@app.route("/api/register/professional", methods=["POST"])
def register_professional():
    """Register a new professional"""
    if professionals is None:
        return jsonify({"message": "Database unavailable"}), 503

    data = request.get_json(silent=True)
    if not data:
        data = request.form.to_dict()

    username = data.get("username")
    password = data.get("password")
    specialty = data.get("specialty", "")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    if professionals.find_one({"username": username}):
        return jsonify({"message": "Username already exists"}), 400

    hashed_pw = generate_password_hash(password, method=HASH_METHOD, salt_length=SALT_LENGTH)
    professionals.insert_one({
        "username": username,
        "password": hashed_pw,
        "specialty": specialty
    })

    return jsonify({"message": "Professional registered successfully!"}), 201


@app.route("/api/verify-token", methods=["GET"])
@token_required
def verify_token():
    """Verify if a token is valid and return user info"""
    return jsonify({
        "valid": True,
        "user": request.current_user
    }), 200


@app.route("/api/protected", methods=["GET"])
@token_required
def protected_route():
    """Example protected route - requires valid JWT token"""
    return jsonify({
        "message": f"Hello {request.current_user['username']}! You have access to this protected route.",
        "role": request.current_user['role']
    }), 200


@app.route("/students", methods=["GET"])
def get_students():
    if students is None:
        return jsonify({"message": "Database unavailable"}), 503

    all_students = []
    for s in students.find():
        s["_id"] = str(s["_id"])
        all_students.append(s)
    return jsonify(all_students), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
