from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

# Import all blueprints
from routs import all_blueprints

app = Flask(__name__)
CORS(app)

# ----- MongoDB connection -----
client = MongoClient("mongodb://127.0.0.1:27017/", serverSelectionTimeoutMS=5000)
db = client["healthDB"]
students = db["students"]
print("✅ Connected to MongoDB!")

# ----- Register Blueprints -----
for bp in all_blueprints:
    app.register_blueprint(bp)

# ----- API Routes (keep these in app.py or move later) -----
@app.route("/register", methods=["POST"])
def register_student():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    tags = data.get("tags", [])
    if not username or not password:
        return jsonify({"message": "Username and password are required"}), 400

    existing = students.find_one({"username": username})
    if existing:
        return jsonify({"message": "Username already exists"}), 400

    hashed_pw = generate_password_hash(password)
    student = {"username": username, "password": hashed_pw, "tags": tags}
    students.insert_one(student)
    return jsonify({"message": "Student registered successfully!"}), 201


@app.route("/students", methods=["GET"])
def get_students():
    all_students = list(students.find({}, {"_id": 0}))
    return jsonify(all_students)

if __name__ == "__main__":
    app.run(port=5000, debug=True)
