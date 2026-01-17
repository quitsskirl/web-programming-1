# =============================================================================
# ROUTES MODULE - routes/__init__.py
# =============================================================================
# Register all route blueprints here.
# Includes both API endpoints and HTML page routes.
# =============================================================================

from .auth_routes import auth_bp
from .classifier_routes import classifier_bp
from .appointments_routes import appointments_bp
from .resources_routes import resources_bp
from .events_routes import events_bp
from .notifications_routes import notifications_bp
from .feedback_routes import feedback_bp
from .page_routes import pages_bp

# All blueprints to register with the app
all_blueprints = [
    # API routes
    auth_bp,
    classifier_bp,
    appointments_bp,
    resources_bp,
    events_bp,
    notifications_bp,
    feedback_bp,
    # Page routes (HTML templates)
    pages_bp,
]
