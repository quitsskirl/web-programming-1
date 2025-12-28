# ==================== IMPORTS ====================
from flask import Flask, request, jsonify  # Flask: web framework, request: get incoming data, jsonify: return JSON responses
from flask_cors import CORS  # CORS: allows frontend (different origin) to call our API
from pymongo import MongoClient  # MongoClient: connects to MongoDB database
from werkzeug.security import generate_password_hash, check_password_hash  # Functions to hash and verify passwords securely
from werkzeug.utils import secure_filename  # Secure filename for uploads
from flask import send_from_directory, make_response  # For serving files

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

# ==================== FILE UPLOAD CONFIGURATION ====================
UPLOAD_FOLDER = os.path.join('static', 'uploads', 'pdfs')
ALLOWED_EXTENSIONS = {'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

# ==================== MONGODB COLLECTIONS (5 tables) ====================
# Table 1: professors - stores professor/counselor account info from sign-in
professors_table = None
# Table 2: appointments - scheduled meetings between students and professionals
appointments = None
# Table 3: resources - articles, videos, coping guides
resources = None
# Table 4: support_tickets - confidential messages to counselors
support_tickets = None
# Table 5: notifications - alerts and reminders for users
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
        
        # ==================== INITIALIZE 5 COLLECTIONS ====================
        # Table 1: professors - professor account info (from sign-in page)
        professors_table = db["professors"]
        # Table 2: appointments - scheduled meetings
        appointments = db["appointments"]
        # Table 3: resources - mental health resources
        resources = db["resources"]
        # Table 4: support_tickets - confidential messages
        support_tickets = db["support_tickets"]
        # Table 5: notifications - user alerts
        notifications = db["notifications"]
        
        # Legacy collections (backward compatibility)
        students = db["students"]
        professionals = db["professionals"]
        
        print("✅ MongoDB connection OK!")
        print("📦 5 tables initialized!")
        
        # ==================== CREATE COLLECTIONS WITH SAMPLE DATA ====================
        # MongoDB collections only appear when they have at least 1 document
        # This ensures all 8 tables show up in MongoDB Atlas
        
        def init_collections():
            """Initialize all 5 collections with sample/schema documents"""
            
            # Table 1: professors - this collection stores professor accounts
            # Data comes from professor registration at /register-professional
            # No sample data needed - real professors will register through the form
            print("   ✓ Table 1: professors - ready")
            
            # Table 2: appointments - sample schema
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
                print("   ✓ Table 2: appointments - created")
            
            # Table 3: resources - sample schema
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
                print("   ✓ Table 3: resources - created")
            
            # Table 4: support_tickets - sample schema (stores classifier results)
            if support_tickets.count_documents({}) == 0:
                support_tickets.insert_one({
                    "_schema": True,
                    "user_id": "sample_user_001",
                    "message": "I've been feeling overwhelmed lately and can't focus on my studies...",
                    "department": "COUNSEL",  # IDC, OPEN, COUNSEL
                    "confidence": 0.85,
                    "crisis": False,
                    "created_at": datetime.datetime.utcnow()
                })
                print("   ✓ Table 4: support_tickets - created")
            
            # Table 5: notifications - sample schema
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
                print("   ✓ Table 5: notifications - created")
            
            print("📊 All 5 tables are now visible in MongoDB Atlas!")
        
        # Run initialization
        init_collections()
        
    except Exception as e:  # Catch any connection errors
        print("❌ MongoDB connection failed:", e)  # Print error message
        client = None
        db = None
        professors_table = None
        appointments = None
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

    # Helper function to save classification to support_tickets
    def save_to_support_tickets(msg, classification_result):
        """Save the message and classification to support_tickets collection"""
        if support_tickets is not None:
            try:
                ticket = {
                    "user_id": request.current_user.get('username'),
                    "message": msg,
                    "department": classification_result.get('department'),
                    "confidence": classification_result.get('confidence'),
                    "crisis": classification_result.get('crisis', False),
                    "created_at": datetime.datetime.utcnow()
                }
                support_tickets.insert_one(ticket)
                print(f"📝 Saved to support_tickets: {classification_result.get('department')}")
            except Exception as e:
                print(f"⚠️ Failed to save to support_tickets: {e}")

    # If no OpenAI client (no key or not installed), directly return fallback
    if not openai_client:
        print("No OPENAI_API_KEY detected — using fallback classifier.")
        result = fallback_classify(message)
        save_to_support_tickets(message, result)  # Save to database
        return jsonify(result)

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
            result = fallback_classify(message)
            save_to_support_tickets(message, result)  # Save to database
            return jsonify(result)

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

        # Save to support_tickets collection
        save_to_support_tickets(message, response)

        return jsonify(response), 200

    except Exception as err:
        # Any error (network, quota, etc.) → use fallback classifier
        print("Classifier error, using fallback:", err)
        result = fallback_classify(message)
        save_to_support_tickets(message, result)  # Save to database
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
    Also returns user profile data (tags, email, bio) from database.
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
    
    # Get user profile data from database
    tags = user.get("tags", [])  # Get tags array from database
    if isinstance(tags, list):
        tags_str = ", ".join(tags) if tags else ""  # Convert list to comma-separated string
    else:
        tags_str = str(tags) if tags else ""
    
    return jsonify({  # Return success response
        "message": "Login successful",
        "token": token,  # JWT token for future authenticated requests
        "user": {
            "username": username,
            "role": "student",
            "tags": tags_str,  # User's tags/interests from database
            "email": user.get("email", ""),  # Email if set
            "bio": user.get("bio", "")  # Bio if set
        }
    }), 200  # 200 = OK


# ----- Professional Login -----
@app.route("/api/login/professional", methods=["POST"])  # POST to /api/login/professional
def login_professional():
    """
    API endpoint to authenticate a professional.
    Same as student login but uses professionals collection.
    Also returns user profile data (specialty, email, bio) from database.
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
        "user": {
            "username": username,
            "role": "professional",
            "specialty": user.get("specialty", ""),  # Professional's specialty from database
            "email": user.get("email", ""),  # Email if set
            "bio": user.get("bio", ""),  # Bio if set
            "availability": user.get("availability", "")  # Availability if set
        }
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
    DELETE operation: Remove a student account and ALL related data from the database.
    
    This completes our CRUD operations:
    - C: Create (register) ✓
    - R: Read (get students) ✓
    - U: Update (above) ✓
    - D: Delete (this function) ✓
    
    URL: DELETE /api/student/delete
    Headers: Authorization: Bearer <token>
    
    IMPORTANT: This permanently deletes the account AND all associated data!
    - Appointments where student is involved
    - Support tickets created by the student
    - Notifications for the student
    """
    if students is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    username = current_user.get('username')
    
    if current_user.get('role') != 'student':
        return jsonify({"message": "Access denied. Only students can delete their account."}), 403
    
    # Track what was deleted for the response
    deleted_data = {
        "appointments": 0,
        "support_tickets": 0,
        "notifications": 0
    }
    
    # 1. Delete all appointments where this student is involved
    if appointments is not None:
        apt_result = appointments.delete_many({"student_username": username})
        deleted_data["appointments"] = apt_result.deleted_count
        print(f"🗑️ Deleted {apt_result.deleted_count} appointments for student: {username}")
    
    # 2. Delete all support tickets created by this student
    if support_tickets is not None:
        # Support tickets use both 'user_id' and 'sender_user_id' fields
        tickets_result = support_tickets.delete_many({
            "$or": [
                {"user_id": username},
                {"sender_user_id": username}
            ]
        })
        deleted_data["support_tickets"] = tickets_result.deleted_count
        print(f"🗑️ Deleted {tickets_result.deleted_count} support tickets for student: {username}")
    
    # 3. Delete all notifications for this student
    if notifications is not None:
        notif_result = notifications.delete_many({"user_id": username})
        deleted_data["notifications"] = notif_result.deleted_count
        print(f"🗑️ Deleted {notif_result.deleted_count} notifications for student: {username}")
    
    # 4. Finally, delete the student account itself
    result = students.delete_one({"username": username})
    
    if result.deleted_count > 0:
        print(f"✅ Student account deleted: {username}")
        return jsonify({
            "message": "Account and all associated data deleted successfully. Sorry to see you go!",
            "deleted_data": deleted_data
        }), 200
    else:
        return jsonify({"message": "Account not found"}), 404


# ----- Delete Professional Account (DELETE operation) -----
@app.route("/api/professional/delete", methods=["DELETE"])
@token_required
def delete_professional():
    """
    DELETE operation: Remove a professional account and ALL related data.
    
    This deletes:
    - The professional account
    - All appointments where professional is involved
    - All resources uploaded by the professional (including PDF files)
    - All notifications for the professional
    """
    if professionals is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    username = current_user.get('username')
    
    if current_user.get('role') != 'professional':
        return jsonify({"message": "Access denied."}), 403
    
    # Track what was deleted for the response
    deleted_data = {
        "appointments": 0,
        "resources": 0,
        "notifications": 0,
        "pdf_files": 0
    }
    
    # 1. Delete all appointments where this professional is involved
    if appointments is not None:
        apt_result = appointments.delete_many({"professional_username": username})
        deleted_data["appointments"] = apt_result.deleted_count
        print(f"🗑️ Deleted {apt_result.deleted_count} appointments for professional: {username}")
    
    # 2. Delete all resources uploaded by this professional
    if resources is not None:
        # First, find all PDF resources to delete their files from the filesystem
        pdf_resources = list(resources.find({
            "uploaded_by": username,
            "resource_type": "pdf"
        }))
        
        # Delete PDF files from the filesystem
        for pdf in pdf_resources:
            if pdf.get("filename"):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], pdf["filename"])
                try:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                        deleted_data["pdf_files"] += 1
                        print(f"🗑️ Deleted PDF file: {filepath}")
                except Exception as e:
                    print(f"⚠️ Could not delete file {filepath}: {e}")
        
        # Delete all resources (PDFs and videos) from database
        res_result = resources.delete_many({"uploaded_by": username})
        deleted_data["resources"] = res_result.deleted_count
        print(f"🗑️ Deleted {res_result.deleted_count} resources for professional: {username}")
    
    # 3. Delete all notifications for this professional
    if notifications is not None:
        notif_result = notifications.delete_many({"user_id": username})
        deleted_data["notifications"] = notif_result.deleted_count
        print(f"🗑️ Deleted {notif_result.deleted_count} notifications for professional: {username}")
    
    # 4. Finally, delete the professional account itself
    result = professionals.delete_one({"username": username})
    
    if result.deleted_count > 0:
        print(f"✅ Professional account deleted: {username}")
        return jsonify({
            "message": "Account and all associated data deleted successfully.",
            "deleted_data": deleted_data
        }), 200
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


# ==================== PDF UPLOAD/DELETE API ====================

# ----- Upload PDF Resource (Professionals only) -----
@app.route("/api/resources/upload-pdf", methods=["POST"])
@token_required
def upload_pdf_resource():
    """
    Upload a PDF file to the server and save metadata to database.
    Only professionals can upload PDFs.
    """
    if resources is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    if current_user.get('role') != 'professional':
        return jsonify({"message": "Only professionals can upload resources"}), 403
    
    # Check if file is in request
    if 'file' not in request.files:
        return jsonify({"message": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"message": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"message": "Only PDF files are allowed"}), 400
    
    # Secure the filename and save
    filename = secure_filename(file.filename)
    # Add timestamp to avoid conflicts
    unique_filename = f"{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    try:
        file.save(filepath)
    except Exception as e:
        return jsonify({"message": f"Failed to save file: {str(e)}"}), 500
    
    # Save metadata to MongoDB
    resource_doc = {
        "title": request.form.get('title', filename.replace('.pdf', '')),
        "description": request.form.get('description', ''),
        "category": request.form.get('category', 'article'),
        "resource_type": "pdf",
        "filename": unique_filename,
        "filepath": f"/static/uploads/pdfs/{unique_filename}",
        "original_filename": filename,
        "uploaded_by": current_user.get('username'),
        "created_at": datetime.datetime.utcnow()
    }
    
    result = resources.insert_one(resource_doc)
    
    return jsonify({
        "message": "PDF uploaded successfully!",
        "resource_id": str(result.inserted_id),
        "filepath": resource_doc["filepath"]
    }), 201


# ----- Update Resource (Professionals only) -----
@app.route("/api/resources/<resource_id>", methods=["PUT"])
@token_required
def update_resource(resource_id):
    """
    UPDATE operation for resources collection.
    Allows professionals to edit resource title and description.
    """
    if resources is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    if current_user.get('role') != 'professional':
        return jsonify({"message": "Only professionals can edit resources"}), 403
    
    # Find the resource
    try:
        resource = resources.find_one({"_id": ObjectId(resource_id)})
    except:
        return jsonify({"message": "Invalid resource ID"}), 400
    
    if not resource:
        return jsonify({"message": "Resource not found"}), 404
    
    # Get update data
    data = request.get_json(silent=True) or {}
    
    update_fields = {}
    
    # Update title if provided
    if "title" in data and data["title"].strip():
        update_fields["title"] = data["title"].strip()
    
    # Update description if provided
    if "description" in data:
        update_fields["description"] = data["description"].strip()
    
    # Update video_url if provided (for video resources)
    if "video_url" in data and data["video_url"].strip():
        update_fields["video_url"] = data["video_url"].strip()
    
    if not update_fields:
        return jsonify({"message": "No fields to update provided"}), 400
    
    # Perform the update
    result = resources.update_one(
        {"_id": ObjectId(resource_id)},
        {"$set": update_fields}
    )
    
    if result.modified_count > 0:
        return jsonify({"message": "Resource updated successfully!", "updated_fields": list(update_fields.keys())}), 200
    else:
        return jsonify({"message": "No changes made (values may be the same)"}), 200


# ----- Delete PDF Resource (Professionals only) -----
@app.route("/api/resources/<resource_id>", methods=["DELETE"])
@token_required
def delete_resource(resource_id):
    """
    Delete a PDF resource from the server and database.
    Only professionals can delete resources.
    """
    if resources is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    if current_user.get('role') != 'professional':
        return jsonify({"message": "Only professionals can delete resources"}), 403
    
    # Find the resource
    try:
        resource = resources.find_one({"_id": ObjectId(resource_id)})
    except:
        return jsonify({"message": "Invalid resource ID"}), 400
    
    if not resource:
        return jsonify({"message": "Resource not found"}), 404
    
    # Delete the file from filesystem if it's a PDF
    if resource.get("resource_type") == "pdf" and resource.get("filename"):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], resource["filename"])
        try: 
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Warning: Could not delete file {filepath}: {e}")
    
    # Delete from database
    result = resources.delete_one({"_id": ObjectId(resource_id)})
    
    if result.deleted_count > 0:
        return jsonify({"message": "Resource deleted successfully!"}), 200
    else:
        return jsonify({"message": "Failed to delete resource"}), 500


# ----- Get PDF Resources (for Resources page) -----
@app.route("/api/resources/pdfs", methods=["GET"])
def get_pdf_resources():
    """
    Get all PDF resources for display on Resources page.
    Public endpoint - no authentication required.
    """
    if resources is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    pdf_resources = []
    for r in resources.find({"resource_type": "pdf"}).sort("created_at", -1):
        r["_id"] = str(r["_id"])
        r["created_at"] = str(r.get("created_at", ""))
        pdf_resources.append(r)
    
    return jsonify(pdf_resources), 200


# ----- Add Video Resource (Professionals only) -----
@app.route("/api/resources/add-video", methods=["POST"])
@token_required
def add_video_resource():
    """
    Add a video resource by providing a URL link.
    Only professionals can add videos.
    """
    if resources is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    current_user = request.current_user
    if current_user.get('role') != 'professional':
        return jsonify({"message": "Only professionals can add resources"}), 403
    
    data = request.get_json(silent=True) or {}
    
    title = data.get('title', '').strip()
    video_url = data.get('video_url', '').strip()
    description = data.get('description', '').strip()
    
    if not title or not video_url:
        return jsonify({"message": "Title and video URL are required"}), 400
    
    # Save video resource to MongoDB
    video_doc = {
        "title": title,
        "description": description,
        "video_url": video_url,
        "resource_type": "video",
        "uploaded_by": current_user.get('username'),
        "created_at": datetime.datetime.utcnow()
    }
    
    result = resources.insert_one(video_doc)
    
    return jsonify({
        "message": "Video added successfully!",
        "resource_id": str(result.inserted_id)
    }), 201


# ----- Get Video Resources (for Resources page) -----
@app.route("/api/resources/videos", methods=["GET"])
def get_video_resources():
    """
    Get all video resources for display on Resources page.
    Public endpoint - no authentication required.
    """
    if resources is None:
        return jsonify({"message": "Database unavailable"}), 503
    
    video_resources = []
    for r in resources.find({"resource_type": "video"}).sort("created_at", -1):
        r["_id"] = str(r["_id"])
        r["created_at"] = str(r.get("created_at", ""))
        video_resources.append(r)
    
    return jsonify(video_resources), 200


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


# ==================== NOTIFICATIONS API ====================

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