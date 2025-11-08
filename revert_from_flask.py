#!/usr/bin/env python3
"""
Revert Flask-style layout back to a flat layout (like your original screenshot).

Usage:
  Dry run (prints the plan):   python revert_from_flask.py
  Apply changes (do the moves): python revert_from_flask.py --apply
  Also remove Flask scaffolding (routes/, utils/, requirements.txt): add --clean
"""
from __future__ import annotations
import argparse
import shutil
from pathlib import Path

ROOT = Path.cwd()
TEMPLATES = ROOT / "templates"
STATIC = ROOT / "static"
CSS = STATIC / "css"
JS = STATIC / "js"

def move_back(src: Path, dst: Path, apply: bool, moves: list[str]):
    """Move a file from src to dst, appending suffixes to avoid overwriting."""
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    final = dst
    i = 1
    while final.exists():
        final = dst.with_name(dst.stem + f"_{i}" + dst.suffix)
        i += 1
    moves.append(f"{src.relative_to(ROOT)}  ->  {final.relative_to(ROOT)}")
    if apply:
        shutil.move(str(src), str(final))

def rmdir_safe(path: Path):
    """Remove directory tree if it exists."""
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Perform the moves.")
    parser.add_argument("--clean", action="store_true", help="Remove Flask scaffolding (routes/, utils/, requirements.txt).")
    args = parser.parse_args()

    moves = []

    # HTML back to root
    if TEMPLATES.exists():
        for f in TEMPLATES.glob("*.html"):
            move_back(f, ROOT / f.name, args.apply, moves)

    # CSS back to root
    if CSS.exists():
        for f in CSS.glob("*.css"):
            move_back(f, ROOT / f.name, args.apply, moves)

    # JS back to root
    if JS.exists():
        for f in JS.glob("*.js"):
            move_back(f, ROOT / f.name, args.apply, moves)

    # --- Report moved files ---
    print("\nPlanned moves:" if not args.apply else "\nMoved:")
    if moves:
        for m in moves:
            print("  ", m)
    else:
        print("  (none)")

    # --- Optionally remove scaffolding ---
    if args.clean:
        print("\nWill remove Flask scaffolding:" if not args.apply else "\nRemoved scaffolding:")
        removed = []
        for path in [ROOT / "routes", ROOT / "utils", ROOT / "model", STATIC, TEMPLATES]:
            if path.exists():
                removed.append(str(path.relative_to(ROOT)))
                if args.apply:
                    rmdir_safe(path)
        req = ROOT / "requirements.txt"
        if req.exists():
            removed.append("requirements.txt")
            if args.apply:
                req.unlink()
        if removed:
            for r in removed:
                print("  ", r)
        else:
            print("  (none)")

    print("\nDone." if args.apply else "\nThis was a dry run. Re-run with --apply to perform changes.")

if __name__ == "__main__":
    main()
