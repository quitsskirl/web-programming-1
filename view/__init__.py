from .first_page import first_bp
from .home import home_bp
from .HPprofessor import hp_professor_bp
from .login_student import login_st_bp
from .login_professional import login_pf_bp
from .more_info import info_bp
from .register_student import register_st_bp
from .register_professional import register_pf_bp
from .services import services_bp
from .settings import settings_bp
from .support_classifier import classifier_bp
from .appointments import appointments_bp
from .resources import resources_bp  # Resources page for students

# Import shared utilities (can be used by any route file)
from .utils import (
    get_current_user,
    get_user_role,
    get_username,
    is_authenticated,
    is_student,
    is_professional,
    login_required,
    student_required,
    professional_required,
    allowed_file,
    allowed_pdf,
    allowed_image,
    validate_required_fields,
    validate_email,
    validate_password,
)


# =============================================================================
# ALL BLUEPRINTS LIST
# =============================================================================
# This list is imported by app.py and used to register all routes at once.
# The order doesn't matter for functionality, but keeping it organized helps.
all_blueprints = [
    first_bp,           # /
    home_bp,            # /home
    hp_professor_bp,    # /home-professor
    login_st_bp,        # /login-student
    login_pf_bp,        # /login-professional
    info_bp,            # /more-info
    register_st_bp,     # /register-student
    register_pf_bp,     # /register-professional
    services_bp,        # /services
    settings_bp,        # /settings, /settings-professor
    classifier_bp,      # /support-classifier
    appointments_bp,    # /book-appointment, /my-appointments
    resources_bp,       # /resources
]
