# =============================================================================
# CLASSIFIER API ROUTES - routes/classifier_routes.py
# =============================================================================
# AI-powered message classification endpoint.
#
# Endpoints:
#   POST /api/classify - Classify student message
#   POST /api/support-ticket - Create support ticket
# =============================================================================

from flask import Blueprint, request, jsonify, current_app
import datetime
import re
import json
import unicodedata

import db  # Import module to get live references after init_db()
from auth.jwt_utils import token_required

classifier_bp = Blueprint("classifier", __name__)


# =============================================================================
# REGEX PATTERNS FOR CLASSIFICATION
# =============================================================================
CRISIS_RE = re.compile(
    r"\b(suicid(e|al)|end(ing)? my life|kill myself|self[-\s]?harm|harm myself|"
    r"hurt myself|overdose|i (want|plan) to die|i don't want to live|i dont want to live)\b",
    re.IGNORECASE,
)

IDC_RE = re.compile(
    r"\b(racist|racial|racism|sexist|sexism|homophob(ic|ia)|transphob(ic|ia)|"
    r"xenophob(ic|ia)|bully|bullied|bullying|harass(ed|ment)?|discriminat(e|ion|ed)|"
    r"slur|hate\s*(speech|crime)|bigot(ed|ry)?)\b",
    re.IGNORECASE,
)

OPEN_RE = re.compile(
    r"\b(assignment(s)?|homework|project(s)?|report(s)?|grade(s)?|mark(s)?|"
    r"exam(s)?|quiz(zes)?|midterm(s)?|final(s)?|deadline(s)?|extension(s)?|"
    r"professor|instructor|teacher|ta\b|course(work)?|syllabus|submit|submission)\b",
    re.IGNORECASE,
)

COUNSEL_RE = re.compile(
    r"\b(alone|lonely|isolated|anxious|anxiety|stress(ed|ful)?|depress(ed|ion|ive)?|"
    r"panic|overwhelmed|burn( |-)?out|can't focus|cant focus|can'?t focus|sad|"
    r"cry(ing)?|hopeless|insomnia|can't sleep|cant sleep|can'?t sleep|sleepless)\b",
    re.IGNORECASE,
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def _normalize_text(msg):
    """Normalize text for classification."""
    text = str(msg or "")
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = text.replace("'", "'")
    return text


def fallback_classify(msg):
    """Local rule-based classifier using regex patterns."""
    text = _normalize_text(msg)

    if CRISIS_RE.search(text):
        return {
            "department": "COUNSEL",
            "confidence": 0.98,
            "reasons": ["Crisis language detected"],
            "crisis": True,
        }

    if IDC_RE.search(text):
        return {
            "department": "IDC",
            "confidence": 0.9,
            "reasons": ["Identity-based harm / bullying keywords"],
            "crisis": False,
        }

    if OPEN_RE.search(text):
        return {
            "department": "OPEN",
            "confidence": 0.85,
            "reasons": ["Academic / course keywords"],
            "crisis": False,
        }

    if COUNSEL_RE.search(text):
        return {
            "department": "COUNSEL",
            "confidence": 0.85,
            "reasons": ["Emotional distress keywords"],
            "crisis": False,
        }

    return {
        "department": "OPEN",
        "confidence": 0.5,
        "reasons": ["No strong signals; defaulting to Open Office"],
        "crisis": False,
    }


def save_to_support_tickets(username, msg, result):
    """Save classification to support_tickets collection."""
    if db.support_tickets is None:
        return
    try:
        ticket = {
            "user_id": username,
            "message": msg,
            "department": result.get('department'),
            "confidence": result.get('confidence'),
            "crisis": result.get('crisis', False),
            "created_at": datetime.datetime.utcnow()
        }
        db.support_tickets.insert_one(ticket)
    except Exception as e:
        print(f"⚠️ Failed to save to support_tickets: {e}")


# =============================================================================
# CLASSIFY MESSAGE ENDPOINT
# =============================================================================
@classifier_bp.route("/api/classify", methods=["POST"])
@token_required
def classify_message():
    """
    Classify a student's message.
    
    Request JSON:
        {"message": "text to classify"}
    
    Response JSON:
        {
            "department": "IDC" | "OPEN" | "COUNSEL",
            "confidence": 0-1,
            "reasons": ["list of reasons"],
            "crisis": true/false
        }
    """
    # Only students can use classifier
    if request.current_user.get('role') != 'student':
        return jsonify({"error": "Only students can use the classifier"}), 403

    data = request.get_json(silent=True) or {}
    message = str(data.get("message", "")).strip()

    if not message:
        return jsonify({"error": "Missing 'message' in request body"}), 400

    # Try OpenAI first, fallback to local classifier
    openai_client = current_app.config.get("OPENAI_CLIENT")
    
    if not openai_client:
        result = fallback_classify(message)
        save_to_support_tickets(request.current_user.get('username'), message, result)
        return jsonify(result), 200

    # OpenAI classification
    system_prompt = """
You are the Student Support Classifier AI.
Analyze the message and classify into one route:

• IDC = discrimination, harassment, racist comments, bullying targeting identity
• OPEN = academic issues, courses, teachers, grades
• COUNSEL = emotional struggles, loneliness, stress, anxiety, depression
• CRISIS = self-harm, suicide, or immediate danger

Output ONLY valid JSON:
{
  "department": "IDC | OPEN | COUNSEL",
  "confidence": 0-1,
  "reasons": ["short bullets"],
  "crisis": true/false
}

Rules:
- Crisis overrides all → department = "COUNSEL" & crisis = true
"""

    try:
        completion = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
        )

        text = (completion.choices[0].message.content or "").strip()
        text = re.sub(r"^```json\s*|\s*```$", "", text)

        try:
            result = json.loads(text)
        except json.JSONDecodeError:
            result = fallback_classify(message)
            save_to_support_tickets(request.current_user.get('username'), message, result)
            return jsonify(result), 200

        # Validate and normalize
        department = result.get("department")
        confidence = result.get("confidence", 0.5)
        reasons = result.get("reasons", [])
        crisis = bool(result.get("crisis", False))

        if department not in ("IDC", "OPEN", "COUNSEL"):
            department = "OPEN"
        if not isinstance(confidence, (int, float)):
            confidence = 0.5
        confidence = max(0.0, min(1.0, float(confidence)))
        if not isinstance(reasons, list):
            reasons = []
        reasons = reasons[:6]
        if crisis:
            department = "COUNSEL"

        response = {
            "department": department,
            "confidence": confidence,
            "reasons": reasons,
            "crisis": crisis,
        }

        save_to_support_tickets(request.current_user.get('username'), message, response)
        return jsonify(response), 200

    except Exception as err:
        print("Classifier error:", err)
        result = fallback_classify(message)
        save_to_support_tickets(request.current_user.get('username'), message, result)
        return jsonify(result), 200


# =============================================================================
# CREATE SUPPORT TICKET
# =============================================================================
@classifier_bp.route("/api/support-ticket", methods=["POST"])
@token_required
def create_support_ticket():
    """Create a support ticket."""
    if db.support_tickets is None:
        return jsonify({"message": "Database unavailable"}), 503

    current_user = request.current_user
    data = request.get_json(silent=True) or {}

    ticket = {
        "ticket_id": f"ticket_{datetime.datetime.utcnow().timestamp()}",
        "sender_user_id": current_user.get('username'),
        "subject": data.get("subject", "Support Request"),
        "message_text": data.get("message"),
        "department": data.get("department"),
        "crisis": data.get("crisis", False),
        "status": "open",
        "sent_at": datetime.datetime.utcnow()
    }

    result = db.support_tickets.insert_one(ticket)

    return jsonify({
        "message": "Support ticket created",
        "ticket_id": str(result.inserted_id)
    }), 201
