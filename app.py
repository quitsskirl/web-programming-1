# =============================================================================
# MENTAL HEALTH SUPPORT PLATFORM - app.py
# =============================================================================
# Main Flask application entry point.
# 
# This is the clean, refactored version with:
# - Configuration in config.py
# - Database in db.py
# - Extensions in extensions.py
# - Auth utilities in auth/jwt_utils.py
# - All routes in routes/
# =============================================================================

from flask import Flask
from dotenv import load_dotenv
import os

# Import configuration and modules
import config
from extensions import cors, create_openai_client
from db import init_db

# Import blueprints (API + Page routes)
from routes import all_blueprints


def create_app():
    """
    Application factory function.
    Creates and configures the Flask application.
    
    Returns:
        Flask app instance
    """
    # Load environment variables from .env file
    load_dotenv()

    # Create Flask app
    app = Flask(__name__)

    # ==========================================================================
    # CONFIGURATION
    # ==========================================================================
    app.config["JWT_SECRET_KEY"] = config.JWT_SECRET_KEY
    app.config["JWT_EXPIRATION_HOURS"] = config.JWT_EXPIRATION_HOURS
    app.config["MAX_CONTENT_LENGTH"] = config.MAX_CONTENT_LENGTH
    app.config["UPLOAD_FOLDER"] = config.UPLOAD_FOLDER
    app.config["EVENT_IMAGES_FOLDER"] = config.EVENT_IMAGES_FOLDER
    
    # Secret key for sessions (if using Flask sessions)
    app.secret_key = config.JWT_SECRET_KEY

    # ==========================================================================
    # EXTENSIONS
    # ==========================================================================
    # Initialize CORS
    cors.init_app(app)

    # ==========================================================================
    # DATABASE
    # ==========================================================================
    # Initialize MongoDB connection
    init_db()

    # ==========================================================================
    # OPENAI CLIENT
    # ==========================================================================
    # Create OpenAI client and store in app config
    app.config["OPENAI_CLIENT"] = create_openai_client()

    # ==========================================================================
    # ENSURE UPLOAD FOLDERS EXIST
    # ==========================================================================
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["EVENT_IMAGES_FOLDER"], exist_ok=True)

    # ==========================================================================
    # REGISTER BLUEPRINTS
    # ==========================================================================
    # Register all routes (API + page routes)
    for bp in all_blueprints:
        app.register_blueprint(bp)

    print("✅ Flask app created successfully!")
    print(f"📁 Upload folder: {app.config['UPLOAD_FOLDER']}")
    print(f"📁 Events folder: {app.config['EVENT_IMAGES_FOLDER']}")

    return app


# =============================================================================
# RUN THE APPLICATION
# =============================================================================
if __name__ == "__main__":
    app = create_app()
    app.run(port=5000, debug=True)
