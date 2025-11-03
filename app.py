from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

app = Flask(__name__)
CORS(app)  # 🔥 this is critical for your browser to connect!

# 🟢 Connect to MongoDB
client = MongoClient("mongodb://127.0.0.1:27017/")
db = client["healthDB"]
students = db["students"]


print("✅ Connected to MongoDB!")

# ---------- ROUTES ---------- #

@app.route("/register", methods=["POST"])
def register_student():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    tags = data.get("tags", [])

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    # Check if username already exists
    if students.find_one({"username": username}):
        return jsonify({"message": "Username already exists"}), 400

    # Hash the password for security
    hashed_pw = generate_password_hash(password)

    # Insert student into MongoDB
    student = {"username": username, "password": hashed_pw, "tags": tags}
    students.insert_one(student)

    return jsonify({"message": "Student registered successfully!"}), 201


@app.route("/students", methods=["GET"])
def get_students():
    """List all registered students (for testing/admin)"""
    all_students = list(students.find({}, {"_id": 0}))
    return jsonify(all_students)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
