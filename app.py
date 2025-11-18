from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv     # ✅ CORRECT
import os
from routs import all_blueprints

app = Flask(__name__)
CORS(app)

# ----- Load Environment Variables -----
load_dotenv()

# ----- MongoDB Atlas Connection -----
client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
db = client["healthDB"]
students = db["students"]

print("✅ Connected to MongoDB Atlas via .env!")

# ----- Register Blueprints -----
for bp in all_blueprints:
    app.register_blueprint(bp)

# ===== API ROUTES =====
@app.route("/register", methods=["POST"])
def register_student():
    data = request.get_json(silent=True) or request.form

    username = data.get("username")
    password = data.get("password")
    tags = data.get("tags", [])

    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    existing = students.find_one({"username": username})
    if existing:
        return jsonify({"message": "Username already exists"}), 400

    hashed_pw = generate_password_hash(password)
    students.insert_one({"username": username, "password": hashed_pw, "tags": tags})

    return jsonify({"message": "Student registered successfully!"}), 201


@app.route("/students", methods=["GET"])
def get_students():
    all_students = list(students.find({}, {"_id": 0}))
    return jsonify(all_students)


if __name__ == "__main__":
    app.run(port=5000, debug=True)
