# =============================================================================
# EXTENSIONS - extensions.py
# =============================================================================
# Flask extensions and external service clients.
# Initialize extensions here, then init with app in create_app().
#
# Usage:
#   from extensions import cors, create_openai_client
# =============================================================================

from flask_cors import CORS
import os

# =============================================================================
# FLASK-CORS
# =============================================================================
# CORS instance - call cors.init_app(app) in create_app()
cors = CORS()


# =============================================================================
# OPENAI CLIENT
# =============================================================================
def create_openai_client():
    """
    Create OpenAI client if API key is available.
    
    Returns:
        OpenAI client or None if no API key
    """
    try:
        from openai import OpenAI
        key = os.getenv("OPENAI_API_KEY")
        if key:
            return OpenAI(api_key=key)
        return None
    except ImportError:
        print("⚠️ OpenAI package not installed. AI classifier will use fallback.")
        return None
