# =============================================================================
# SUPPORT CLASSIFIER ROUTE - support_classifier.py
# =============================================================================
# AI-powered message classifier that routes student concerns to the right
# department (IDC, OPEN, COUNSEL).
#
# URL: /support-classifier
# TEMPLATE: SupportClassifier.html
#
# CLASSIFICATION CATEGORIES:
# - IDC: Identity-based discrimination, harassment, bullying
# - OPEN: Academic issues, grades, courses, assignments
# - COUNSEL: Emotional struggles, stress, anxiety, depression
# - CRISIS: Self-harm, suicide → routes to COUNSEL with crisis=True
# =============================================================================

from flask import Blueprint, render_template, request
import re
import unicodedata

# Create Blueprint
classifier_bp = Blueprint('classifier', __name__)


# =============================================================================
# CLASSIFICATION REGEX PATTERNS (from app.py)
# =============================================================================
# Pre-compiled regex patterns for efficient matching

# CRISIS: Immediate danger, self-harm, suicide
CRISIS_RE = re.compile(
    r"\b(suicid(e|al)|end(ing)? my life|kill myself|self[-\s]?harm|harm myself|"
    r"hurt myself|overdose|i (want|plan) to die|i don't want to live|"
    r"i dont want to live)\b",
    re.IGNORECASE,
)

# IDC: Identity-based discrimination, harassment, bullying
IDC_RE = re.compile(
    r"\b(racist|racial|racism|sexist|sexism|homophob(ic|ia)|transphob(ic|ia)|"
    r"xenophob(ic|ia)|bully|bullied|bullying|harass(ed|ment)?|"
    r"discriminat(e|ion|ed)|slur|hate\s*(speech|crime)|bigot(ed|ry)?)\b",
    re.IGNORECASE,
)

# OPEN: Academic issues, grades, assignments
OPEN_RE = re.compile(
    r"\b(assignment(s)?|homework|project(s)?|report(s)?|grade(s)?|mark(s)?|"
    r"exam(s)?|quiz(zes)?|midterm(s)?|final(s)?|deadline(s)?|extension(s)?|"
    r"professor|instructor|teacher|ta\b|course(work)?|syllabus|submit|submission)\b",
    re.IGNORECASE,
)

# COUNSEL: Emotional distress, mental health
COUNSEL_RE = re.compile(
    r"\b(alone|lonely|isolated|anxious|anxiety|stress(ed|ful)?|"
    r"depress(ed|ion|ive)?|panic|overwhelmed|burn( |-)?out|can't focus|"
    r"cant focus|can'?t focus|sad|cry(ing)?|hopeless|insomnia|"
    r"can't sleep|cant sleep|can'?t sleep|sleepless)\b",
    re.IGNORECASE,
)


# =============================================================================
# CLASSIFICATION KEYWORDS (simplified version)
# =============================================================================
URGENT_KEYWORDS = ["suicide", "kill myself", "self harm", "self-harm", "end my life"]
ANXIETY_KEYWORDS = ["panic", "anxiety", "anxious", "stress", "stressed", "overwhelmed"]
ACADEMIC_KEYWORDS = ["study", "exam", "grades", "assignment", "homework", "professor"]
DEPRESSION_KEYWORDS = ["depressed", "depression", "sad", "lonely", "hopeless"]


# =============================================================================
# SUPPORT INFORMATION
# =============================================================================
SUPPORT_INFO = {
    "IDC": {
        "title": "Identity & Discrimination Support",
        "description": "Our IDC team handles cases of discrimination, harassment, and bullying.",
        "action": "Connect with IDC representative",
        "color": "warning",
        "icon": "bi-shield-exclamation"
    },
    "OPEN": {
        "title": "Academic Support (Open Office)",
        "description": "Our academic advisors can help with course and grade concerns.",
        "action": "Contact Academic Office",
        "color": "primary",
        "icon": "bi-mortarboard"
    },
    "COUNSEL": {
        "title": "Counseling Services",
        "description": "Our mental health professionals are here to help.",
        "action": "Book a counseling session",
        "color": "info",
        "icon": "bi-heart"
    },
    "CRISIS": {
        "title": "⚠️ Crisis Support",
        "description": "If you're in immediate danger, please reach out now.",
        "action": "Call 988 (Suicide & Crisis Lifeline)",
        "color": "danger",
        "icon": "bi-exclamation-triangle-fill"
    }
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def normalize_text(msg):
    """
    Normalize text for classification:
    - Convert to string
    - Normalize unicode (NFKD)
    - Lowercase
    - Replace smart quotes with normal apostrophes
    
    Args:
        msg: Input message text
    
    Returns:
        str: Normalized text
    """
    text = str(msg or "")
    text = unicodedata.normalize("NFKD", text)
    text = text.lower()
    text = text.replace("'", "'")
    return text


def fallback_classify(msg):
    """
    Local rule-based classifier using regex patterns.
    
    This is the fallback when OpenAI is not available.
    Uses keyword groups to decide:
    - IDC: identity-based harm / bullying / harassment
    - OPEN: academic / grading / course issues
    - COUNSEL: emotional wellbeing
    - CRISIS: self-harm / suicide → COUNSEL + crisis=True
    
    Args:
        msg: The student's message text
    
    Returns:
        dict: Classification result with:
            - department: "IDC" | "OPEN" | "COUNSEL"
            - confidence: float between 0 and 1
            - reasons: list of explanation strings
            - crisis: bool
    """
    text = normalize_text(msg)
    
    # Crisis overrides everything
    if CRISIS_RE.search(text):
        print("🧭 Fallback matched: CRISIS")
        return {
            "department": "COUNSEL",
            "confidence": 0.98,
            "reasons": ["Crisis language detected - immediate support needed"],
            "crisis": True,
        }
    
    # IDC = identity-based discrimination / bullying / harassment
    if IDC_RE.search(text):
        print("🧭 Fallback matched: IDC")
        return {
            "department": "IDC",
            "confidence": 0.9,
            "reasons": ["Identity-based harm / bullying / harassment keywords detected"],
            "crisis": False,
        }
    
    # OPEN = academic issues, grades, assignments, etc.
    if OPEN_RE.search(text):
        print("🧭 Fallback matched: OPEN")
        return {
            "department": "OPEN",
            "confidence": 0.85,
            "reasons": ["Academic / grading / course keywords detected"],
            "crisis": False,
        }
    
    # COUNSEL = emotional distress, stress, anxiety, etc.
    if COUNSEL_RE.search(text):
        print("🧭 Fallback matched: COUNSEL")
        return {
            "department": "COUNSEL",
            "confidence": 0.85,
            "reasons": ["Emotional distress / wellbeing keywords detected"],
            "crisis": False,
        }
    
    # Default when nothing matches strongly
    print("🧭 Fallback matched: DEFAULT → OPEN")
    return {
        "department": "OPEN",
        "confidence": 0.5,
        "reasons": ["No strong signals detected - routing to Open Office"],
        "crisis": False,
    }


def classify_message_simple(text):
    """
    Simple keyword-based classifier (for demo purposes).
    
    Args:
        text: The student's message text
    
    Returns:
        str: Classification category (urgent, anxiety, academic, depression, general)
    """
    if not text:
        return "general"
    
    t = text.lower()
    
    # Check for urgent/crisis keywords first (highest priority)
    if any(keyword in t for keyword in URGENT_KEYWORDS):
        return "urgent"
    
    # Check for mental health keywords
    if any(keyword in t for keyword in ANXIETY_KEYWORDS):
        return "anxiety"
    
    if any(keyword in t for keyword in DEPRESSION_KEYWORDS):
        return "depression"
    
    # Check for academic keywords
    if any(keyword in t for keyword in ACADEMIC_KEYWORDS):
        return "academic"
    
    # Default to general support
    return "general"


def get_support_info(department):
    """
    Get support information based on classification department.
    
    Args:
        department: The classification department (IDC, OPEN, COUNSEL)
    
    Returns:
        dict: Support information with title, description, action, color, icon
    """
    if department == "COUNSEL" and True:  # Check for crisis flag if needed
        pass
    return SUPPORT_INFO.get(department, SUPPORT_INFO["OPEN"])


def get_crisis_resources():
    """
    Get crisis resources for immediate help.
    
    Returns:
        list: Crisis hotline information
    """
    return [
        {
            "name": "988 Suicide & Crisis Lifeline",
            "number": "988",
            "description": "24/7 free and confidential support"
        },
        {
            "name": "Crisis Text Line",
            "number": "Text HOME to 741741",
            "description": "Free 24/7 crisis support via text"
        },
        {
            "name": "Campus Emergency",
            "number": "Your campus emergency number",
            "description": "For immediate campus assistance"
        }
    ]


# =============================================================================
# ROUTE HANDLERS
# =============================================================================
@classifier_bp.route('/support-classifier', methods=['GET', 'POST'])
def support_classifier_page():
    """
    Display the Student Support Classifier tool.
    
    URL: http://localhost:5000/support-classifier
    
    GET: Display the classifier form
    POST: Classify the submitted message using the local fallback classifier
    
    The page can also call the /api/classify endpoint for AI classification.
    
    Form Data Expected (POST):
        - message: The student's concern/message text
    
    Returns:
        Rendered SupportClassifier.html template with classification result
    """
    result = None
    message = ""
    support_info = None
    crisis_resources = None
    
    if request.method == 'POST':
        message = request.form.get('message', '')
        
        # Use the regex-based classifier
        classification = fallback_classify(message)
        
        result = classification
        support_info = get_support_info(classification['department'])
        
        # If crisis detected, include crisis resources
        if classification.get('crisis'):
            crisis_resources = get_crisis_resources()
            support_info = SUPPORT_INFO["CRISIS"]
    
    return render_template(
        'SupportClassifier.html', 
        result=result, 
        message=message,
        support_info=support_info,
        crisis_resources=crisis_resources
    )


@classifier_bp.route('/support', methods=['GET', 'POST'])
def support():
    """
    Alternative support classifier URL.
    
    URL: http://localhost:5000/support
    
    Same as support_classifier_page but with shorter URL.
    """
    return support_classifier_page()
