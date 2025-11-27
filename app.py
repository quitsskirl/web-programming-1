from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv
import os
from routs import all_blueprints

app = Flask(__name__)
CORS(app)

# Load Environment Variables
load_dotenv()

# MongoDB Connection
client = MongoClient(
    os.getenv("MONGO_URI"),
    tls=True,
    tlsAllowInvalidCertificates=True
)
db = client["healthDB"]
students = db["students"]

# Test Connection
try:
    client.admin.command("ping")
    print("✅ MongoDB connection OK!")
except Exception as e:
    print("❌ MongoDB connection failed:", e)

# Register Blueprints
for bp in all_blueprints:
    app.register_blueprint(bp)

# ===== ROUTES =====
@app.route("/register", methods=["POST"])
def register_student():
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

    hashed_pw = generate_password_hash(password)
    students.insert_one({"username": username, "password": hashed_pw, "tags": tags})

    return jsonify({"message": "Student registered successfully!"}), 201


@app.route("/students", methods=["GET"])
def get_students():
    all_students = []
    for s in students.find():
        s["_id"] = str(s["_id"])
        all_students.append(s)
    return jsonify(all_students), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
