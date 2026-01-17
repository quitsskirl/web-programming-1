# =============================================================================
# CONFIGURATION - config.py
# =============================================================================
# All application configuration in one place.
# Import this module to access any config value.
#
# Usage:
#   from config import JWT_SECRET_KEY, UPLOAD_FOLDER
# =============================================================================

import os

# =============================================================================
# PASSWORD HASHING
# =============================================================================
HASH_METHOD = "scrypt"  # Memory-hard algorithm, resistant to brute-force
SALT_LENGTH = 16  # Bytes of random salt added to password

# =============================================================================
# FILE UPLOAD PATHS
# =============================================================================
UPLOAD_FOLDER = os.path.join("static", "uploads", "pdfs")
EVENT_IMAGES_FOLDER = os.path.join("static", "uploads", "events")

# =============================================================================
# ALLOWED FILE EXTENSIONS
# =============================================================================
ALLOWED_PDF_EXTENSIONS = {"pdf"}
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# =============================================================================
# JWT CONFIGURATION
# =============================================================================
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_EXPIRATION_HOURS = 24
JWT_ALGORITHM = "HS256"

# =============================================================================
# FILE SIZE LIMITS
# =============================================================================
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

# =============================================================================
# OPENAI CONFIGURATION
# =============================================================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def allowed_file(filename, allowed_extensions=None):
    """Check if file extension is allowed."""
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_PDF_EXTENSIONS
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def allowed_pdf(filename):
    """Check if file is a PDF."""
    return allowed_file(filename, ALLOWED_PDF_EXTENSIONS)


def allowed_image(filename):
    """Check if file is an image."""
    return allowed_file(filename, ALLOWED_IMAGE_EXTENSIONS)
