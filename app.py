# ==================== IMPORTS ====================
from flask import Flask, request, jsonify  # Flask: web framework, request: get incoming data, jsonify: return JSON responses
from flask_cors import CORS  # CORS: allows frontend (different origin) to call our API
from pymongo import MongoClient  # MongoClient: connects to MongoDB database
from werkzeug.security import generate_password_hash, check_password_hash  # Functions to hash and verify passwords securely

# Password hashing configuration
HASH_METHOD = 'scrypt'  # scrypt: memory-hard algorithm, resistant to brute-force attacks
SALT_LENGTH = 16  # 16 bytes of random data added to password before hashing

from dotenv import load_dotenv  # load_dotenv: reads variables from .env file into environment
from functools import wraps  # wraps: preserves original function name/docstring when using decorators
import os  # os: access environment variables with os.getenv()
import jwt  # jwt: create and verify JSON Web Tokens for authentication
import datetime  # datetime: calculate token expiration times
from routs import all_blueprints  # all_blueprints: list of all page routes (login, home, etc.)

# Imports for AI classifier (OpenAI + helpers)
from openai import OpenAI  # OpenAI: Python client to call GPT models
import json  # json: parse/encode JSON when reading model responses
import re  # re: regular expressions for local fallback classifier
import unicodedata  # unicodedata: normalize unicode text (e.g. smart quotes)


# ==================== APP SETUP ====================
load_dotenv()  # Read .env file and load MONGO_URI, JWT_SECRET_KEY, OPENAI_API_KEY into os.environ

app = Flask(__name__)  # Create the Flask application instance (__name__ = current module)
CORS(app)  # Enable Cross-Origin Resource Sharing so frontend can make API calls

# ==================== JWT CONFIGURATION ====================
# JWT Configuration - stored in app.config for easy access throughout the app
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production')  # Secret key used to sign tokens (get from .env or use default)
app.config['JWT_EXPIRATION_HOURS'] = 24  # Tokens expire after 24 hours


# ==================== OPENAI CONFIGURATION ====================
# OPENAI_API_KEY is stored in .env and loaded via load_dotenv() above
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # Your OpenAI API key (do NOT hardcode in source)
openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None  # Create OpenAI client if key present


# ==================== JWT FUNCTIONS ====================
def generate_token(user_id, username, role='student'):
    """
    Creates a JWT token containing user information.
    This token is sent to the client and used for authentication.
    """
    payload = {  # payload: data stored inside the token
        'user_id': str(user_id),  # Convert MongoDB ObjectId to string for JSON compatibility
        'username': username,  # Store username so we know who the token belongs to
        'role': role,  # 'student' or 'professional' - determines access level
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=app.config['JWT_EXPIRATION_HOURS']),  # exp: expiration time (now + 24 hours)
        'iat': datetime.datetime.utcnow()  # iat: issued at time (when token was created)
    }
    return jwt.encode(payload, app.config['JWT_SECRET_KEY'], algorithm='HS256')  # Encode payload with secret key using HMAC-SHA256


def token_required(f):
    """
    Decorator function that protects routes.
    Add @token_required above any route that needs authentication.
    If no valid token, returns 401 Unauthorized.
    """
    @wraps(f)  # Preserve the original function's name and docstring
    def decorated(*args, **kwargs):  # Wrapper function that runs before the actual route
        token = None  # Initialize token as None
        
        # Method 1: Check Authorization header (standard way)
        # Format: "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
        if 'Authorization' in request.headers:  # Check if Authorization header exists
            auth_header = request.headers['Authorization']  # Get the header value
            if auth_header.startswith('Bearer '):  # Check it starts with "Bearer "
                token = auth_header.split(' ')[1]  # Extract token (everything after "Bearer ")
        
        # Method 2: Check URL query parameter (fallback)
        # Format: /api/endpoint?token=eyJhbGciOiJIUzI1NiIs...
        if not token:  # If no token found in header
            token = request.args.get('token')  # Check URL query params
        
        # No token found anywhere = unauthorized
        if not token:
            return jsonify({'message': 'Token is missing'}), 401  # 401 = Unauthorized
        
        # Verify the token is valid and not expired
        try:
            payload = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])  # Decode and verify token
            request.current_user = payload  # Attach user info to request object for use in route
        except jwt.ExpiredSignatureError:  # Token's exp time has passed
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:  # Token is malformed or signature doesn't match
            return jsonify({'message': 'Invalid token'}), 401
        
        return f(*args, **kwargs)  # Token valid - call the actual route function
    return decorated  # Return the wrapper function


# ==================== DATABASE CONNECTION ====================
mongo_uri = os.getenv("MONGO_URI")  # Get connection string from environment (set in .env file)
client = None  # MongoDB client object (will hold connection)
db = None  # Database reference
students = None  # Collection for student documents
professionals = None  # Collection for professional documents

if mongo_uri:  # Only try to connect if MONGO_URI is set
    try:
        # Create MongoDB client with connection options
        client = MongoClient(
            mongo_uri,  # Connection string: mongodb+srv://user:pass@cluster.mongodb.net/ or mongodb://127.0.0.1:27017/
            tls=True,  # Use TLS encryption for secure connection
            tlsAllowInvalidCertificates=True,  # Allow self-signed certificates (development)
            serverSelectionTimeoutMS=5000  # Wait max 5 seconds to find server
        )
        client.admin.command("ping")  # Send ping to test if connection works
        db = client["healthDB"]  # Select/create database named "healthDB"
        students = db["students"]  # Reference to "students" collection
        professionals = db["professionals"]  # Reference to "professionals" collection
        print("✅ MongoDB connection OK!")  # Success message
    except Exception as e:  # Catch any connection errors
        print("❌ MongoDB connection failed:", e)  # Print error message
        client = None  # Reset all variables to None
        db = None
        students = None
        professionals = None
else:
    print("⚠️ MONGO_URI not set. Database features will be unavailable.")  # Warning if no connection string


# ==================== REGISTER BLUEPRINTS ====================
# Blueprints are modular route files (login_student.py, home.py, etc.)
# This loop registers each blueprint so Flask knows about those routes
for bp in all_blueprints:  # Iterate through list of blueprints
    app.register_blueprint(bp)  # Register each blueprint with the Flask app


# ==================== LOCAL FALLBACK CLASSIFIER (NO OPENAI NEEDED) ====================
def _normalize_text(msg):
    """
    Helper to normalize text:
    - convert to string
    - normalize unicode (NFKD)
    - lowercase
    - replace smart quotes with normal apostrophes
    """
    text = str(msg or "")
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = text.replace("’", "'")
    return text


# Pre-compiled regex patterns to match categories
CRISIS_RE = re.compile(
    r"\b(suicid(e|al)|end(ing)? my life|kill myself|self[-\s]?harm|harm myself|hurt myself|overdose|"
    r"i (want|plan) to die|i don't want to live|i dont want to live)\b",
    re.IGNORECASE,
)

IDC_RE = re.compile(
    r"\b(racist|racial|racism|sexist|sexism|homophob(ic|ia)|transphob(ic|ia)|xenophob(ic|ia)|"
    r"bully|bullied|bullying|harass(ed|ment)?|discriminat(e|ion|ed)|slur|hate\s*(speech|crime)|"
    r"bigot(ed|ry)?)\b",
    re.IGNORECASE,
)

OPEN_RE = re.compile(
    r"\b(assignment(s)?|homework|project(s)?|report(s)?|grade(s)?|mark(s)?|exam(s)?|quiz(zes)?|"
    r"midterm(s)?|final(s)?|deadline(s)?|extension(s)?|professor|instructor|teacher|ta\b|"
    r"course(work)?|syllabus|submit|submission)\b",
    re.IGNORECASE,
)

COUNSEL_RE = re.compile(
    r"\b(alone|lonely|isolated|anxious|anxiety|stress(ed|ful)?|depress(ed|ion|ive)?|panic|"
    r"overwhelmed|burn( |-)?out|can't focus|cant focus|can'?t focus|sad|cry(ing)?|hopeless|"
    r"insomnia|can't sleep|cant sleep|can'?t sleep|sleepless)\b",
    re.IGNORECASE,
)


def fallback_classify(msg):
    """
    Local rule-based classifier that mimics your Node.js fallback:
    - Uses keyword groups to decide:
      - IDC: identity-based harm / bullying / harassment
      - OPEN: academic / grading / course issues
      - COUNSEL: emotional wellbeing
      - CRISIS: self-harm / suicide → COUNSEL + crisis=True

    Returns a dictionary with:
    {
      "department": "IDC" | "OPEN" | "COUNSEL",
      "confidence": float between 0 and 1,
      "reasons": [list of short strings],
      "crisis": bool
    }
    """
    text = _normalize_text(msg)

    # Crisis overrides everything
    if CRISIS_RE.search(text):
        print("🧭 Fallback matched: CRISIS")
        return {
            "department": "COUNSEL",
            "confidence": 0.98,
            "reasons": ["Crisis language detected"],
            "crisis": True,
        }

    # IDC = identity-based discrimination / bullying / harassment
    if IDC_RE.search(text):
        print("🧭 Fallback matched: IDC")
        return {
            "department": "IDC",
            "confidence": 0.9,
            "reasons": ["Identity-based harm / bullying / harassment keywords"],
            "crisis": False,
        }

    # OPEN = academic issues, grades, assignments, etc.
    if OPEN_RE.search(text):
        print("🧭 Fallback matched: OPEN")
        return {
            "department": "OPEN",
            "confidence": 0.85,
            "reasons": ["Academic / grading / course keywords"],
            "crisis": False,
        }

    # COUNSEL = emotional distress, stress, anxiety, etc.
    if COUNSEL_RE.search(text):
        print("🧭 Fallback matched: COUNSEL")
        return {
            "department": "COUNSEL",
            "confidence": 0.85,
            "reasons": ["Emotional distress / wellbeing keywords"],
            "crisis": False,
        }

    # Default when nothing matches strongly
    print("🧭 Fallback matched: DEFAULT → OPEN")
    return {
        "department": "OPEN",
        "confidence": 0.5,
        "reasons": ["No strong signals; defaulting to Open Office"],
        "crisis": False,
    }


# ==================== AI CLASSIFIER API ROUTE ====================
@app.route("/api/classify", methods=["POST"])
def classify_message():
    """
    API endpoint to classify a free-text student message.

    URL: POST /api/classify

    Request JSON:
        {
          "message": "free text from student"
        }

    Response JSON:
        {
          "department": "IDC" | "OPEN" | "COUNSEL",
          "confidence": 0-1,
          "reasons": ["short bullets"],
          "crisis": true/false
        }

    Behavior:
    - If OPENAI_API_KEY is not configured or the API fails, we use fallback_classify().
    - If OpenAI works, we use GPT (gpt-4o-mini) to classify and enforce JSON output.
    """
    # Read JSON body (silent=True to avoid exceptions if invalid)
    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Missing 'message' in request body."}), 400

    # System prompt used with GPT model (same logic as Node version)
    system_prompt = """
You are the Student Support Classifier AI.
Analyze the message and classify into one route:

• IDC = discrimination, harassment, racist comments, bullying targeting identity
• OPEN = academic issues, courses, teachers, grades
• COUNSEL = emotional struggles, loneliness, stress, anxiety, depression
• CRISIS = self-harm, suicide, or immediate danger

Output ONLY valid JSON:
{
  "department": "IDC | OPEN | COUNSEL",
  "confidence": 0-1,
  "reasons": ["short bullets"],
  "crisis": true/false
}

Rules:
- Crisis overrides all → department = "COUNSEL" & crisis = true
"""

    # If no OpenAI client (no key or not installed), directly return fallback
    if not openai_client:
        print("No OPENAI_API_KEY detected — using fallback classifier.")
        return jsonify(fallback_classify(message))

    try:
        # Call OpenAI Chat Completion API
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Lightweight, cost-effective model
            temperature=0.1,  # Low temperature → more deterministic output
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
        )

        # Extract text from first choice
        text = (completion.choices[0].message.content or "").strip()

        # Remove ```json ... ``` wrappers if present
        text = re.sub(r"^```json\s*|\s*```$", "", text)

        # Parse JSON returned by the model
        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            # If model response is not valid JSON, fall back to local classifier
            print("Model returned invalid JSON. Using fallback. Raw:", text)
            return jsonify(fallback_classify(message))

        # Normalize and validate response structure
        department = result.get("department")
        confidence = result.get("confidence", 0.5)
        reasons = result.get("reasons", [])
        crisis = bool(result.get("crisis", False))

        # Ensure department is one of the allowed values
        if department not in ("IDC", "OPEN", "COUNSEL"):
            department = "OPEN"

        # Ensure confidence is a float between 0 and 1
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
        confidence = max(0.0, min(1.0, float(confidence)))

        # Ensure reasons is a short list
        if not isinstance(reasons, list):
            reasons = []
        reasons = reasons[:6]  # Cap at 6 reasons

        # Crisis rule: if crisis is true, department is always COUNSEL
        if crisis:
            department = "COUNSEL"

        response = {
            "department": department,
            "confidence": confidence,
            "reasons": reasons,
            "crisis": crisis,
        }

        return jsonify(response), 200

    except Exception as err:
        # Any error (network, quota, etc.) → use fallback classifier
        print("Classifier error, using fallback:", err)
        return jsonify(fallback_classify(message)), 200


# ==================== API ROUTES (USER AUTH + DATA) ====================

# ----- Student Registration -----
@app.route("/register", methods=["POST"])  # Route decorator: POST requests to /register
def register_student():
    """
    API endpoint to create a new student account.
    Expects JSON or form data with: username, password, tags (optional)
    """
    if students is None:  # Check if database is connected
        return jsonify({"message": "Database unavailable"}), 503  # 503 = Service Unavailable

    # Get request data - try JSON first, then form data
    data = request.get_json(silent=True)  # Try to parse JSON body (silent=True prevents error if not JSON)
    if not data:  # If no JSON data
        data = request.form.to_dict()  # Get form data as dictionary

    username = data.get("username")  # Extract username from data (None if not present)
    password = data.get("password")  # Extract password from data
    tags = data.get("tags", [])  # Extract tags, default to empty list if not provided

    if not isinstance(tags, list):  # If tags is not a list (e.g., single string)
        tags = [tags]  # Convert to list

    # Validation
    if not username or not password:  # Check required fields exist
        return jsonify({"message": "Username and password are required"}), 400  # 400 = Bad Request

    # Check username availability
    if students.find_one({"username": username}):  # Search for existing user with same username
        return jsonify({"message": "Username already exists"}), 400  # Username taken

    # Hash password and save to database
    hashed_pw = generate_password_hash(password, method=HASH_METHOD, salt_length=SALT_LENGTH)  # Hash with scrypt + salt
    students.insert_one({"username": username, "password": hashed_pw, "tags": tags})  # Insert document into MongoDB

    return jsonify({"message": "Student registered successfully!"}), 201  # 201 = Created


# ----- Student Login -----
@app.route("/api/login/student", methods=["POST"])  # POST to /api/login/student
def login_student():
    """
    API endpoint to authenticate a student.
    Returns JWT token if credentials are valid.
    """
    if students is None:  # Check database connection
        return jsonify({"message": "Database unavailable"}), 503

    data = request.get_json(silent=True)  # Try JSON body
    if not data:
        data = request.form.to_dict()  # Fallback to form data

    username = data.get("username")  # Get submitted username
    password = data.get("password")  # Get submitted password

    if not username or not password:  # Validate required fields
        return jsonify({"message": "Username and password are required"}), 400

    # Find user in database
    user = students.find_one({"username": username})  # Query MongoDB for user
    if not user:  # No user found with that username
        return jsonify({"message": "Invalid username or password"}), 401  # 401 = Unauthorized (generic error for security)

    # Verify password
    if not check_password_hash(user.get("password", ""), password):  # Compare submitted password with stored hash
        return jsonify({"message": "Invalid username or password"}), 401  # Wrong password

    # Generate JWT token
    token = generate_token(user["_id"], username, role='student')  # Create token with user info
    
    return jsonify({  # Return success response
        "message": "Login successful",
        "token": token,  # JWT token for future authenticated requests
        "user": {"username": username, "role": "student"}  # User info for frontend
    }), 200  # 200 = OK


# ----- Professional Login -----
@app.route("/api/login/professional", methods=["POST"])  # POST to /api/login/professional
def login_professional():
    """
    API endpoint to authenticate a professional.
    Same as student login but uses professionals collection.
    """
    if professionals is None:
        return jsonify({"message": "Database unavailable"}), 503

    data = request.get_json(silent=True)
    if not data:
        data = request.form.to_dict()

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    user = professionals.find_one({"username": username})  # Search professionals collection
    if not user:
        return jsonify({"message": "Invalid username or password"}), 401

    if not check_password_hash(user.get("password", ""), password):
        return jsonify({"message": "Invalid username or password"}), 401

    token = generate_token(user["_id"], username, role='professional')  # role='professional' for different access
    
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {"username": username, "role": "professional"}
    }), 200


# ----- Professional Registration -----
@app.route("/api/register/professional", methods=["POST"])  # POST to /api/register/professional
def register_professional():
    """
    API endpoint to create a new professional account.
    Includes optional specialty field.
    """
    if professionals is None:
        return jsonify({"message": "Database unavailable"}), 503

    data = request.get_json(silent=True)
    if not data:
        data = request.form.to_dict()

    username = data.get("username")
    password = data.get("password")
    specialty = data.get("specialty", "")  # Optional: professional's area of expertise

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    if professionals.find_one({"username": username}):  # Check username not taken
        return jsonify({"message": "Username already exists"}), 400

    hashed_pw = generate_password_hash(password, method=HASH_METHOD, salt_length=SALT_LENGTH)
    professionals.insert_one({  # Insert professional document
        "username": username,
        "password": hashed_pw,
        "specialty": specialty
    })

    return jsonify({"message": "Professional registered successfully!"}), 201


# ----- Token Verification -----
@app.route("/api/verify-token", methods=["GET"])  # GET request to /api/verify-token
@token_required  # Decorator: must provide valid token to access this route
def verify_token():
    """
    API endpoint to check if a token is still valid.
    Used by frontend to verify user is still logged in.
    """
    return jsonify({
        "valid": True,  # If we reach here, token was valid (otherwise decorator returned 401)
        "user": request.current_user  # Return decoded user info from token
    }), 200


# ----- Protected Route Example -----
@app.route("/api/protected", methods=["GET"])  # Example protected route
@token_required  # Requires authentication
def protected_route():
    """
    Example of a protected API route.
    Demonstrates how to access user info from token.
    """
    return jsonify({
        "message": f"Hello {request.current_user['username']}! You have access.",  # Access username from decoded token
        "role": request.current_user['role']  # Access role from decoded token
    }), 200


# ----- Get All Students (Debug) -----
@app.route("/students", methods=["GET"])  # GET request to /students
def get_students():
    """
    API endpoint to fetch all students.
    WARNING: Should be protected in production!
    """
    if students is None:
        return jsonify({"message": "Database unavailable"}), 503

    all_students = []  # List to hold all student documents
    for s in students.find():  # Iterate through all documents in students collection
        s["_id"] = str(s["_id"])  # Convert MongoDB ObjectId to string (ObjectId not JSON serializable)
        all_students.append(s)  # Add document to list
    return jsonify(all_students), 200  # Return list as JSON


# ==================== START SERVER ====================
if __name__ == "__main__":  # Only run if this file is executed directly (not imported)
    app.run(port=5000, debug=True)  # Start Flask dev server on port 5000 with debug mode (auto-reload on changes)
