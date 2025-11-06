from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

app = Flask(__name__)
CORS(app)  # 🔥 this is critical for your browser to connect!

try:
    # 🟢 Connect to MongoDB with error handling
    client = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=5000)
    # Test the connection
    client.server_info()
    db = client["healthDB"]
    students = db["students"]
    print("✅ Connected to MongoDB!")

except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    # You may want to exit the app or handle the error differently
    raise

# ---------- ROUTES ---------- #

@app.route("/register", methods=["POST"])
def register_student():
    try:
        data = request.json
        print("DEBUG: /register called with JSON:", data)

        username = data.get("username")
        password = data.get("password")
        tags = data.get("tags", [])
        print(f"DEBUG: parsed username={username!r}, tags={tags!r}, password_provided={'yes' if password else 'no'}")

        if not username or not password:
            print("DEBUG: missing username or password")
            return jsonify({"message": "Username and password are required"}), 400

        # Check if username already exists
        existing = students.find_one({"username": username})
        print(f"DEBUG: existing user lookup result: {existing is not None}")
        if existing:
            print(f"DEBUG: username '{username}' already exists")
            return jsonify({"message": "Username already exists"}), 400

        # Hash the password for security
        hashed_pw = generate_password_hash(password)
        print("DEBUG: password hashed (value not printed for security)")

        # Insert student into MongoDB
        student = {"username": username, "password": hashed_pw, "tags": tags}
        result = students.insert_one(student)
        print(f"DEBUG: inserted student with _id={result.inserted_id}")

        return jsonify({"message": "Student registered successfully!"}), 201


    except Exception as e:
        print(f"❌ Error in register_student: {e}")
        return jsonify({"message": "Internal server error"}), 500


@app.route("/students", methods=["GET"])
def get_students():
    """List all registered students (for testing/admin)"""
    try:
        all_students = list(students.find({}, {"_id": 0}))
        return jsonify(all_students)
    except Exception as e:
        print(f"❌ Error in get_students: {e}")
        return jsonify({"message": "Internal server error"}), 500


if __name__ == "__main__":
    app.run(port=5000, debug=True)