#!/usr/bin/env python3
"""
Reorganize a flat web project into a Flask-style structure.

Usage:
  Dry run (shows what will happen):   python reorganize_to_flask.py
  Apply changes (perform moves):      python reorganize_to_flask.py --apply
"""
from __future__ import annotations
import argparse
import shutil
from pathlib import Path

ROOT = Path.cwd()

TEMPLATES_DIR = ROOT / "templates"
STATIC_DIR = ROOT / "static"
CSS_DIR = STATIC_DIR / "css"
JS_DIR = STATIC_DIR / "js"
ROUTES_DIR = ROOT / "routes"
MODEL_DIR = ROOT / "model"
UTILS_DIR = ROOT / "utils"

# File-name clues to route grouping (optional; purely to create example blueprints)
AUTH_HINTS = {"login", "register", "registration"}
HOME_HINTS = {"home", "firstpage", "moreinfo", "services", "settings"}

def ensure_dirs():
    for d in [TEMPLATES_DIR, CSS_DIR, JS_DIR, ROUTES_DIR, MODEL_DIR, UTILS_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    # package markers
    for d in [ROUTES_DIR, MODEL_DIR, UTILS_DIR]:
        (d / "__init__.py").touch(exist_ok=True)

def move_if_exists(src: Path, dst: Path, apply: bool, moves: list[str]):
    if not src.exists() or not src.is_file():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    # avoid overwriting: if target exists, add a numeric suffix
    final_dst = dst
    i = 1
    while final_dst.exists():
        final_dst = dst.with_name(dst.stem + f"_{i}" + dst.suffix)
        i += 1
    moves.append(f"{src.relative_to(ROOT)}  ->  {final_dst.relative_to(ROOT)}")
    if apply:
        shutil.move(str(src), str(final_dst))

def discover_files():
    html, css, js, py = [], [], [], []
    for p in ROOT.glob("*"):
        if not p.is_file():
            continue
        if p.name.startswith("."):
            continue
        if p.suffix.lower() == ".html":
            html.append(p)
        elif p.suffix.lower() == ".css":
            css.append(p)
        elif p.suffix.lower() == ".js":
            js.append(p)
        elif p.suffix.lower() == ".py":
            # we'll preserve .py in place except generate boilerplate if missing
            py.append(p)
    return html, css, js, py

def write_if_missing(path: Path, content: str, apply: bool, created: list[str]):
    if path.exists():
        return
    created.append(f"CREATE {path.relative_to(ROOT)}")
    if apply:
        path.write_text(content, encoding="utf-8")

def guess_group(name: str) -> str:
    n = name.lower()
    if any(h in n for h in AUTH_HINTS):
        return "auth"
    if any(h in n for h in HOME_HINTS):
        return "home"
    return "home"

AUTH_BLUEPRINT = """from flask import Blueprint, render_template

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    return render_template('loginST.html')

@auth_bp.route('/register')
def register():
    return render_template('registerST.html')
"""

HOME_BLUEPRINT = """from flask import Blueprint, render_template

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def home():
    return render_template('HomePage.html')
"""

APP_PY = """from flask import Flask
from routes.auth_routes import auth_bp
from routes.home_routes import home_bp

app = Flask(__name__)
app.register_blueprint(auth_bp)
app.register_blueprint(home_bp)

if __name__ == "__main__":
    app.run(debug=True)
"""

UTIL_AUTH = """# Put shared auth helpers here (password hashing, validators, etc.)
"""

REQS = "Flask>=3.0\n"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Perform the moves (otherwise just print the plan).")
    args = parser.parse_args()

    ensure_dirs()

    html, css, js, py = discover_files()
    moves, creates = [], []

    # Move assets
    for f in html:
        move_if_exists(f, TEMPLATES_DIR / f.name, args.apply, moves)
    for f in css:
        move_if_exists(f, CSS_DIR / f.name, args.apply, moves)
    for f in js:
        move_if_exists(f, JS_DIR / f.name, args.apply, moves)

    # Boilerplate (only if missing)
    write_if_missing(ROUTES_DIR / "auth_routes.py", AUTH_BLUEPRINT, args.apply, creates)
    write_if_missing(ROUTES_DIR / "home_routes.py", HOME_BLUEPRINT, args.apply, creates)
    write_if_missing(ROOT / "app.py", APP_PY, args.apply, creates)
    write_if_missing(UTILS_DIR / "auth.py", UTIL_AUTH, args.apply, creates)
    write_if_missing(ROOT / "requirements.txt", REQS, args.apply, creates)

    # Summary
    print("\nPlanned moves:" if not args.apply else "\nMoved:")
    if moves:
        for m in moves:
            print("  ", m)
    else:
        print("  (none)")

    print("\nPlanned file creations:" if not args.apply else "\nCreated:")
    if creates:
        for c in creates:
            print("  ", c)
    else:
        print("  (none)")

    print("\nDone." if args.apply else "\nThis was a dry run. Re-run with --apply to perform changes.")

if __name__ == "__main__":
    main()
