import os
from flask import Flask, g
from flask_cors import CORS
from pymongo import MongoClient

def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    CORS(app)

    # ---- MongoDB setup (one client for the whole app) ----
    mongo_uri = os.getenv("MONGO_URI", "mongodb://127.0.0.1:27017/")
    try:
        client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        client.server_info()  # test connection
        db = client["healthDB"]
        app.config["MONGO_CLIENT"] = client
        app.config["MONGO_DB"] = db
        print("✅ Connected to MongoDB!")
    except Exception as e:
        print(f"❌ Error connecting to MongoDB: {e}")
        raise

    # Make the DB available on `g.db` for every request
    @app.before_request
    def _attach_db():
        g.db = app.config["MONGO_DB"]

    # ---- Blueprints ----
    from routes.home_routes import home_bp
    from routes.auth_routes import auth_bp

    app.register_blueprint(home_bp)                 # e.g. "/", "/home", etc.
    app.register_blueprint(auth_bp, url_prefix="/auth")  # e.g. "/auth/login"

    # Health check (optional)
    @app.get("/healthz")
    def healthz():
        return {"ok": True}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(port=5000, debug=True)
