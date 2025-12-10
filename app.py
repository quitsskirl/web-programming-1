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

# ==================== MONGODB COLLECTIONS (8 tables) ====================
# Table 1: users - general account info (students + professionals)
users = None
# Table 2: user_profiles - personal details (age, department, emergency contact)
user_profiles = None
# Table 3: appointments - scheduled meetings between students and professionals
appointments = None
# Table 4: mood_logs - daily mood tracking entries
mood_logs = None
# Table 5: assessments - self-evaluation tests and surveys
assessments = None
# Table 6: resources - articles, videos, coping guides
resources = None
# Table 7: support_tickets - confidential messages to counselors
support_tickets = None
# Table 8: notifications - alerts and reminders for users
notifications = None

# Legacy collections (for backward compatibility with existing code)
students = None
professionals = None

if mongo_uri:  # Only try to connect if MONGO_URI is set
    try:
        # Create MongoDB client with connection options
        client = MongoClient(
            mongo_uri,  # Connection string: mongodb+srv://user:pass@cluster.mongodb.net/
            tls=True,  # Use TLS encryption for secure connection
            tlsAllowInvalidCertificates=True,  # Allow self-signed certificates (development)
            serverSelectionTimeoutMS=5000  # Wait max 5 seconds to find server
        )
        client.admin.command("ping")  # Send ping to test if connection works
        db = client["healthDB"]  # Select/create database named "healthDB"
        
        # ==================== INITIALIZE 8 COLLECTIONS ====================
        # Table 1: users - general account info
        users = db["users"]
        # Table 2: user_profiles - personal details
        user_profiles = db["user_profiles"]
        # Table 3: appointments - scheduled meetings
        appointments = db["appointments"]
        # Table 4: mood_logs - daily mood tracking
        mood_logs = db["mood_logs"]
        # Table 5: assessments - self-evaluation tests
        assessments = db["assessments"]
        # Table 6: resources - mental health resources
        resources = db["resources"]
        # Table 7: support_tickets - confidential messages
        support_tickets = db["support_tickets"]
        # Table 8: notifications - user alerts
        notifications = db["notifications"]
        
        # Legacy collections (backward compatibility)
        students = db["students"]
        professionals = db["professionals"]
        
        print("✅ MongoDB connection OK!")
        print("📦 8 tables initialized!")
        
        # ==================== CREATE COLLECTIONS WITH SAMPLE DATA ====================
        # MongoDB collections only appear when they have at least 1 document
        # This ensures all 8 tables show up in MongoDB Atlas
        
        def init_collections():
            """Initialize all 8 collections with sample/schema documents"""
            
            # Table 1: users - sample schema
            if users.count_documents({}) == 0:
                users.insert_one({
                    "_schema": True,  # Mark as schema document
                    "user_id": "sample_user_001",
                    "name": "Sample User",
                    "email": "sample@example.com",
                    "password_hash": "hashed_password_here",
                    "role": "student",  # student or professional
                    "created_at": datetime.datetime.utcnow(),
                    "status": "active"  # active, inactive, suspended
                })
                print("   ✓ Table 1: users - created")
            
            # Table 2: user_profiles - sample schema
            if user_profiles.count_documents({}) == 0:
                user_profiles.insert_one({
                    "_schema": True,
                    "profile_id": "sample_profile_001",
                    "user_id": "sample_user_001",
                    "age": 20,
                    "gender": "prefer_not_to_say",
                    "department": "Computer Science",
                    "academic_year": "2nd Year",
                    "contact_info": "+1234567890",
                    "emergency_contact": "+0987654321"
                })
                print("   ✓ Table 2: user_profiles - created")
            
            # Table 3: appointments - sample schema
            if appointments.count_documents({}) == 0:
                appointments.insert_one({
                    "_schema": True,
                    "appointment_id": "sample_apt_001",
                    "student_id": "sample_user_001",
                    "professional_id": "sample_prof_001",
                    "appointment_date": datetime.datetime.utcnow(),
                    "status": "pending",  # pending, confirmed, completed, cancelled
                    "notes": "Initial consultation"
                })
                print("   ✓ Table 3: appointments - created")
            
            # Table 4: mood_logs - sample schema
            if mood_logs.count_documents({}) == 0:
                mood_logs.insert_one({
                    "_schema": True,
                    "entry_id": "sample_mood_001",
                    "user_id": "sample_user_001",
                    "mood_level": 7,  # 1-10 scale
                    "notes": "Feeling okay today",
                    "logged_at": datetime.datetime.utcnow()
                })
                print("   ✓ Table 4: mood_logs - created")
            
            # Table 5: assessments - sample schema
            if assessments.count_documents({}) == 0:
                assessments.insert_one({
                    "_schema": True,
                    "assessment_id": "sample_assess_001",
                    "user_id": "sample_user_001",
                    "date_taken": datetime.datetime.utcnow(),
                    "score": 75,
                    "assessment_type": "anxiety_screening",  # anxiety_screening, depression_screening, stress_test
                    "comments": "Mild anxiety detected"
                })
                print("   ✓ Table 5: assessments - created")
            
            # Table 6: resources - sample schema
            if resources.count_documents({}) == 0:
                resources.insert_one({
                    "_schema": True,
                    "resource_id": "sample_resource_001",
                    "title": "Coping with Stress",
                    "resource_type": "article",  # article, video, guide
                    "description": "Tips for managing academic stress",
                    "link_url": "https://example.com/stress-tips",
                    "created_by": "sample_prof_001",
                    "created_at": datetime.datetime.utcnow()
                })
                print("   ✓ Table 6: resources - created")
            
            # Table 7: support_tickets - sample schema
            if support_tickets.count_documents({}) == 0:
                support_tickets.insert_one({
                    "_schema": True,
                    "ticket_id": "sample_ticket_001",
                    "sender_user_id": "sample_user_001",
                    "receiver_user_id": "sample_prof_001",
                    "subject": "Need someone to talk to",
                    "message_text": "I've been feeling overwhelmed lately...",
                    "sent_at": datetime.datetime.utcnow(),
                    "status": "open",  # open, in_progress, resolved
                    "department": "COUNSEL",  # IDC, OPEN, COUNSEL
                    "crisis": False
                })
                print("   ✓ Table 7: support_tickets - created")
            
            # Table 8: notifications - sample schema
            if notifications.count_documents({}) == 0:
                notifications.insert_one({
                    "_schema": True,
                    "notification_id": "sample_notif_001",
                    "user_id": "sample_user_001",
                    "title": "Welcome to Mental Health Support",
                    "message": "Thank you for joining our platform!",
                    "type": "welcome",  # welcome, appointment, reminder, message
                    "read": False,
                    "created_at": datetime.datetime.utcnow()
                })
                print("   ✓ Table 8: notifications - created")
            
            print("📊 All 8 tables are now visible in MongoDB Atlas!")
        
        # Run initialization
        init_collections()
        
    except Exception as e:  # Catch any connection errors
        print("❌ MongoDB connection failed:", e)  # Print error message
        client = None
        db = None
        users = None
        user_profiles = None
        appointments = None
        mood_logs = None
        assessments = None
        resources = None
        support_tickets = None
        notifications = None
        students = None
        professionals = None
else:
    print("⚠️ MONGO_URI not set. Database features will be unavailable.")


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
@token_required  # Require valid JWT token
def classify_message():
    """
    API endpoint to classify a free-text student message.
    PROTECTED: Only authenticated students can access this endpoint.

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
    # Check if user is a student (only students can use the classifier)
    if request.current_user.get('role') != 'student':
        return jsonify({"error": "Access denied. Only students can use the classifier."}), 403

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


# ==================== CRUD OPERATIONS ====================
# CRUD = Create, Read, Update, Delete - the 4 basic database operations
# We need full CRUD for the project requirements

# Import ObjectId for MongoDB document lookups by _id
from bson import ObjectId  # ObjectId: MongoDB's unique identifier type


# ==================== UPDATE OPERATIONS ====================

# ----- Update Student Profile (UPDATE operation) -----
@app.route("/api/student/update", methods=["PUT"])  # PUT request for updating data
@token_required  # User must be logged in
def update_student():
    """
    UPDATE operation: Modify an existing student's profile.
    
    This is one of the 4 CRUD operations required for the project.
    - C: Create (register) ✓
    - R: Read (get students) ✓
    - U: Update (this function) ✓
    - D: Delete (below) ✓
    
    URL: PUT /api/student/update
    Headers: Authorization: Bearer <token>
    
    Request JSON:
        {
            "tags": ["new", "tags"],      // Optional: update interests/tags
            "email": "new@email.com"      // Optional: update email
        }
    
    Response: Success or error message
    """
    if students is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    # Get current user from JWT token (set by @token_required decorator)
    current_user = request.current_user
    username = current_user.get('username')
    
    # Only students can update student profiles
    if current_user.get('role') != 'student':
        return jsonify({"message": "Access denied. Only students can update their profile."}), 403
    
    # Get update data from request body
    data = request.get_json(silent=True) or {}
    
    # Build update document - only include fields that were provided
    update_fields = {}
    
    if "tags" in data:  # Update tags/interests if provided
        tags = data["tags"]
        if not isinstance(tags, list):  # Ensure tags is a list
            tags = [tags]
        update_fields["tags"] = tags
    
    if "email" in data:  # Update email if provided
        update_fields["email"] = data["email"]
    
    if "bio" in data:  # Update bio/description if provided
        update_fields["bio"] = data["bio"]
    
    # Check if there's anything to update
    if not update_fields:
        return jsonify({"message": "No fields to update provided"}), 400
    
    # Perform the UPDATE operation in MongoDB
    # update_one() finds one document and updates it
    result = students.update_one(
        {"username": username},  # Filter: find document with this username
        {"$set": update_fields}  # Update: set the new field values
    )
    
    # Check if update was successful
    if result.modified_count > 0:
        return jsonify({"message": "Profile updated successfully!", "updated_fields": list(update_fields.keys())}), 200
    else:
        return jsonify({"message": "No changes made (profile may already have these values)"}), 200


# ----- Update Professional Profile (UPDATE operation) -----
@app.route("/api/professional/update", methods=["PUT"])
@token_required
def update_professional():
    """
    UPDATE operation: Modify an existing professional's profile.
    Similar to student update but for professionals.
    """
    if professionals is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    username = current_user.get('username')
    
    if current_user.get('role') != 'professional':
        return jsonify({"message": "Access denied. Only professionals can update their profile."}), 403
    
    data = request.get_json(silent=True) or {}
    update_fields = {}
    
    if "specialty" in data:
        update_fields["specialty"] = data["specialty"]
    
    if "email" in data:
        update_fields["email"] = data["email"]
    
    if "bio" in data:
        update_fields["bio"] = data["bio"]
    
    if "availability" in data:  # Professionals can set availability
        update_fields["availability"] = data["availability"]
    
    if not update_fields:
        return jsonify({"message": "No fields to update provided"}), 400
    
    result = professionals.update_one(
        {"username": username},
        {"$set": update_fields}
    )
    
    if result.modified_count > 0:
        return jsonify({"message": "Profile updated successfully!"}), 200
    else:
        return jsonify({"message": "No changes made"}), 200


# ==================== DELETE OPERATIONS ====================

# ----- Delete Student Account (DELETE operation) -----
@app.route("/api/student/delete", methods=["DELETE"])  # DELETE request for removing data
@token_required
def delete_student():
    """
    DELETE operation: Remove a student account from the database.
    
    This completes our CRUD operations:
    - C: Create (register) ✓
    - R: Read (get students) ✓
    - U: Update (above) ✓
    - D: Delete (this function) ✓
    
    URL: DELETE /api/student/delete
    Headers: Authorization: Bearer <token>
    
    IMPORTANT: This permanently deletes the account!
    """
    if students is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    username = current_user.get('username')
    
    if current_user.get('role') != 'student':
        return jsonify({"message": "Access denied. Only students can delete their account."}), 403
    
    # Perform the DELETE operation in MongoDB
    # delete_one() finds and removes one document
    result = students.delete_one({"username": username})
    
    if result.deleted_count > 0:
        return jsonify({"message": "Account deleted successfully. Sorry to see you go!"}), 200
    else:
        return jsonify({"message": "Account not found"}), 404


# ----- Delete Professional Account (DELETE operation) -----
@app.route("/api/professional/delete", methods=["DELETE"])
@token_required
def delete_professional():
    """
    DELETE operation: Remove a professional account.
    """
    if professionals is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    username = current_user.get('username')
    
    if current_user.get('role') != 'professional':
        return jsonify({"message": "Access denied."}), 403
    
    result = professionals.delete_one({"username": username})
    
    if result.deleted_count > 0:
        return jsonify({"message": "Account deleted successfully."}), 200
    else:
        return jsonify({"message": "Account not found"}), 404


# ==================== ADDITIONAL COLLECTION ROUTES ====================
# These routes demonstrate CRUD operations on other collections

# ----- Create Appointment (CREATE for appointments collection) -----
@app.route("/api/appointments", methods=["POST"])
@token_required
def create_appointment():
    """
    CREATE operation for appointments collection.
    Allows students to book appointments with professionals.
    """
    if appointments is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    data = request.get_json(silent=True) or {}
    
    # Create appointment document
    appointment = {
        "student_username": current_user.get('username'),
        "professional_username": data.get("professional"),
        "date": data.get("date"),
        "time": data.get("time"),
        "reason": data.get("reason", ""),
        "status": "pending",  # pending, confirmed, completed, cancelled
        "created_at": datetime.datetime.utcnow()
    }
    
    result = appointments.insert_one(appointment)
    
    return jsonify({
        "message": "Appointment requested!",
        "appointment_id": str(result.inserted_id)
    }), 201


# ----- Get Appointments (READ for appointments collection) -----
@app.route("/api/appointments", methods=["GET"])
@token_required
def get_appointments():
    """
    READ operation for appointments collection.
    Returns appointments for the logged-in user.
    """
    if appointments is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    username = current_user.get('username')
    role = current_user.get('role')
    
    # Find appointments based on user role
    if role == 'student':
        query = {"student_username": username}
    else:
        query = {"professional_username": username}
    
    user_appointments = []
    for apt in appointments.find(query):
        apt["_id"] = str(apt["_id"])
        apt["created_at"] = str(apt.get("created_at", ""))
        user_appointments.append(apt)
    
    return jsonify(user_appointments), 200


# ----- Get Resources (READ for resources collection) -----
@app.route("/api/resources", methods=["GET"])
def get_resources():
    """
    READ operation for resources collection.
    Returns mental health resources (public, no auth required).
    """
    if resources is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    all_resources = []
    for r in resources.find():
        r["_id"] = str(r["_id"])
        all_resources.append(r)
    
    return jsonify(all_resources), 200


# ----- Add Resource (CREATE for resources collection - professionals only) -----
@app.route("/api/resources", methods=["POST"])
@token_required
def add_resource():
    """
    CREATE operation for resources collection.
    Only professionals can add resources.
    """
    if resources is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    if current_user.get('role') != 'professional':
        return jsonify({"message": "Only professionals can add resources"}), 403
    
    data = request.get_json(silent=True) or {}
    
    resource = {
        "title": data.get("title"),
        "content": data.get("content"),
        "category": data.get("category", "general"),  # stress, anxiety, depression, etc.
        "added_by": current_user.get('username'),
        "created_at": datetime.datetime.utcnow()
    }
    
    resources.insert_one(resource)
    
    return jsonify({"message": "Resource added successfully!"}), 201


# ----- Create Support Ticket (CREATE for support_tickets collection) -----
@app.route("/api/support-ticket", methods=["POST"])
@token_required
def create_support_ticket():
    """
    CREATE operation for support_tickets collection.
    Creates a support ticket from the classifier results.
    """
    if support_tickets is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    data = request.get_json(silent=True) or {}
    
    ticket = {
        "ticket_id": f"ticket_{datetime.datetime.utcnow().timestamp()}",
        "sender_user_id": current_user.get('username'),
        "subject": data.get("subject", "Support Request"),
        "message_text": data.get("message"),
        "department": data.get("department"),  # IDC, OPEN, COUNSEL
        "crisis": data.get("crisis", False),
        "status": "open",  # open, in_progress, resolved
        "sent_at": datetime.datetime.utcnow()
    }
    
    result = support_tickets.insert_one(ticket)
    
    return jsonify({
        "message": "Support ticket created",
        "ticket_id": str(result.inserted_id)
    }), 201


# ==================== MOOD LOGS API (Table 4) ====================

# ----- Create Mood Log Entry -----
@app.route("/api/mood-logs", methods=["POST"])
@token_required
def create_mood_log():
    """
    CREATE: Log a daily mood entry.
    Students can track their mood over time.
    """
    if mood_logs is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    data = request.get_json(silent=True) or {}
    
    entry = {
        "entry_id": f"mood_{datetime.datetime.utcnow().timestamp()}",
        "user_id": current_user.get('username'),
        "mood_level": data.get("mood_level", 5),  # 1-10 scale
        "notes": data.get("notes", ""),
        "logged_at": datetime.datetime.utcnow()
    }
    
    mood_logs.insert_one(entry)
    return jsonify({"message": "Mood logged successfully!"}), 201


# ----- Get Mood Logs -----
@app.route("/api/mood-logs", methods=["GET"])
@token_required
def get_mood_logs():
    """
    READ: Get all mood logs for the current user.
    """
    if mood_logs is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    username = current_user.get('username')
    
    # Find all mood logs for this user, sorted by date (newest first)
    logs = []
    for log in mood_logs.find({"user_id": username}).sort("logged_at", -1):
        log["_id"] = str(log["_id"])
        log["logged_at"] = str(log.get("logged_at", ""))
        logs.append(log)
    
    return jsonify(logs), 200


# ==================== ASSESSMENTS API (Table 5) ====================

# ----- Submit Assessment -----
@app.route("/api/assessments", methods=["POST"])
@token_required
def submit_assessment():
    """
    CREATE: Submit a mental health assessment/survey.
    """
    if assessments is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    data = request.get_json(silent=True) or {}
    
    assessment = {
        "assessment_id": f"assess_{datetime.datetime.utcnow().timestamp()}",
        "user_id": current_user.get('username'),
        "date_taken": datetime.datetime.utcnow(),
        "score": data.get("score", 0),
        "assessment_type": data.get("type", "general"),  # anxiety, depression, stress
        "answers": data.get("answers", []),  # Store individual answers
        "comments": data.get("comments", "")
    }
    
    assessments.insert_one(assessment)
    return jsonify({"message": "Assessment submitted successfully!"}), 201


# ----- Get Assessments -----
@app.route("/api/assessments", methods=["GET"])
@token_required
def get_assessments():
    """
    READ: Get all assessments for the current user.
    """
    if assessments is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    username = current_user.get('username')
    
    user_assessments = []
    for a in assessments.find({"user_id": username}).sort("date_taken", -1):
        a["_id"] = str(a["_id"])
        a["date_taken"] = str(a.get("date_taken", ""))
        user_assessments.append(a)
    
    return jsonify(user_assessments), 200


# ==================== USER PROFILES API (Table 2) ====================

# ----- Create/Update User Profile -----
@app.route("/api/profile", methods=["POST", "PUT"])
@token_required
def update_user_profile():
    """
    CREATE/UPDATE: Create or update user profile with personal details.
    """
    if user_profiles is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    data = request.get_json(silent=True) or {}
    
    profile_data = {
        "user_id": current_user.get('username'),
        "age": data.get("age"),
        "gender": data.get("gender"),
        "department": data.get("department"),
        "academic_year": data.get("academic_year"),
        "contact_info": data.get("contact_info"),
        "emergency_contact": data.get("emergency_contact"),
        "updated_at": datetime.datetime.utcnow()
    }
    
    # Remove None values
    profile_data = {k: v for k, v in profile_data.items() if v is not None}
    
    # Upsert: update if exists, insert if not
    user_profiles.update_one(
        {"user_id": current_user.get('username')},
        {"$set": profile_data},
        upsert=True
    )
    
    return jsonify({"message": "Profile updated successfully!"}), 200


# ----- Get User Profile -----
@app.route("/api/profile", methods=["GET"])
@token_required
def get_user_profile():
    """
    READ: Get the current user's profile.
    """
    if user_profiles is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    profile = user_profiles.find_one({"user_id": current_user.get('username')})
    
    if profile:
        profile["_id"] = str(profile["_id"])
        return jsonify(profile), 200
    else:
        return jsonify({"message": "Profile not found"}), 404


# ==================== NOTIFICATIONS API (Table 8) ====================

# ----- Get Notifications -----
@app.route("/api/notifications", methods=["GET"])
@token_required
def get_notifications():
    """
    READ: Get all notifications for the current user.
    """
    if notifications is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    username = current_user.get('username')
    
    user_notifications = []
    for n in notifications.find({"user_id": username}).sort("created_at", -1):
        n["_id"] = str(n["_id"])
        n["created_at"] = str(n.get("created_at", ""))
        user_notifications.append(n)
    
    return jsonify(user_notifications), 200


# ----- Mark Notification as Read -----
@app.route("/api/notifications/<notification_id>/read", methods=["PUT"])
@token_required
def mark_notification_read(notification_id):
    """
    UPDATE: Mark a notification as read.
    """
    if notifications is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    result = notifications.update_one(
        {"_id": ObjectId(notification_id)},
        {"$set": {"read": True}}
    )
    
    if result.modified_count > 0:
        return jsonify({"message": "Notification marked as read"}), 200
    else:
        return jsonify({"message": "Notification not found"}), 404


# ----- Create Notification (Internal use) -----
def create_notification(user_id, title, message, notif_type="general"):
    """
    Helper function to create notifications.
    Called internally when events happen (appointments, messages, etc.)
    """
    if notifications is None:
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
    
    return notifications.insert_one(notif)


# ==================== START SERVER ====================
if __name__ == "__main__":  # Only run if this file is executed directly (not imported)
    app.run(port=5000, debug=True)  # Start Flask dev server on port 5000 with debug mode (auto-reload on changes)
