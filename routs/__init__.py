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

# List of all blueprints for easy registration
all_blueprints = [
    first_bp,
    home_bp,
    hp_professor_bp,
    login_st_bp,
    login_pf_bp,
    info_bp,
    register_st_bp,
    register_pf_bp,
    services_bp,
    settings_bp,
]
