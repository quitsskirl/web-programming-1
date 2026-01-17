# =============================================================================
# DATABASE - db.py
# =============================================================================
# MongoDB connection and collections.
# Call init_db() once when app starts.
#
# Usage:
#   from db import students, professionals, appointments
# =============================================================================

from pymongo import MongoClient
import os
import datetime

# =============================================================================
# CONNECTION OBJECTS
# =============================================================================
client = None
db = None

# =============================================================================
# COLLECTIONS (Tables)
# =============================================================================
# These will be initialized in init_db()

# User collections
students = None
professionals = None
professors_table = None  # Alias for professionals

# Feature collections
appointments = None
resources = None
support_tickets = None
notifications = None
event_images = None
feedback = None


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================
def init_db():
    """
    Initialize MongoDB connection and collections.
    
    Call this once when the app starts.
    Collections will be None if connection fails.
    """
    global client, db
    global students, professionals, professors_table
    global appointments, resources, support_tickets
    global notifications, event_images, feedback

    mongo_uri = os.getenv("MONGO_URI")
    
    if not mongo_uri:
        print("⚠️ MONGO_URI not set. Database features will be unavailable.")
        return False

    try:
        # Create MongoDB client
        client = MongoClient(
            mongo_uri,
            tls=True,
            tlsAllowInvalidCertificates=True,
            serverSelectionTimeoutMS=5000
        )
        
        # Test connection
        client.admin.command("ping")
        
        # Select database
        db = client["healthDB"]

        # Initialize collections
        students = db["students"]
        professionals = db["professionals"]
        professors_table = db["professors"]  # Alias
        
        appointments = db["appointments"]
        resources = db["resources"]
        support_tickets = db["support_tickets"]
        notifications = db["notifications"]
        event_images = db["event_images"]
        feedback = db["feedback"]

        print("✅ MongoDB connection OK!")
        print("📦 Collections initialized!")
        
        # Initialize sample data if needed
        _init_sample_data()
        
        return True

    except Exception as e:
        print("❌ MongoDB connection failed:", e)
        _reset_collections()
        return False


def _reset_collections():
    """Reset all collection references to None on connection failure."""
    global client, db
    global students, professionals, professors_table
    global appointments, resources, support_tickets
    global notifications, event_images, feedback
    
    client = None
    db = None
    students = None
    professionals = None
    professors_table = None
    appointments = None
    resources = None
    support_tickets = None
    notifications = None
    event_images = None
    feedback = None


def _init_sample_data():
    """Initialize collections with sample/schema documents if empty."""
    
    # Appointments - sample schema
    if appointments is not None and appointments.count_documents({}) == 0:
        appointments.insert_one({
            "_schema": True,
            "appointment_id": "sample_apt_001",
            "student_id": "sample_user_001",
            "professional_id": "sample_prof_001",
            "appointment_date": datetime.datetime.utcnow(),
            "status": "pending",
            "notes": "Initial consultation"
        })
        print("   ✓ appointments - schema created")
    
    # Resources - sample schema
    if resources is not None and resources.count_documents({}) == 0:
        resources.insert_one({
            "_schema": True,
            "resource_id": "sample_resource_001",
            "title": "Coping with Stress",
            "resource_type": "article",
            "description": "Tips for managing academic stress",
            "link_url": "https://example.com/stress-tips",
            "created_by": "sample_prof_001",
            "created_at": datetime.datetime.utcnow()
        })
        print("   ✓ resources - schema created")
    
    # Support tickets - sample schema
    if support_tickets is not None and support_tickets.count_documents({}) == 0:
        support_tickets.insert_one({
            "_schema": True,
            "user_id": "sample_user_001",
            "message": "Sample support ticket",
            "department": "COUNSEL",
            "confidence": 0.85,
            "crisis": False,
            "created_at": datetime.datetime.utcnow()
        })
        print("   ✓ support_tickets - schema created")
    
    # Notifications - sample schema
    if notifications is not None and notifications.count_documents({}) == 0:
        notifications.insert_one({
            "_schema": True,
            "notification_id": "sample_notif_001",
            "user_id": "sample_user_001",
            "title": "Welcome to Mental Health Support",
            "message": "Thank you for joining our platform!",
            "type": "welcome",
            "read": False,
            "created_at": datetime.datetime.utcnow()
        })
        print("   ✓ notifications - schema created")


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def is_db_available():
    """Check if database connection is available."""
    return db is not None


def get_collection(name):
    """
    Get a collection by name.
    
    Args:
        name: Collection name ('students', 'appointments', etc.)
    
    Returns:
        Collection object or None
    """
    collections = {
        'students': students,
        'professionals': professionals,
        'professors': professors_table,
        'appointments': appointments,
        'resources': resources,
        'support_tickets': support_tickets,
        'notifications': notifications,
        'event_images': event_images,
        'feedback': feedback,
    }
    return collections.get(name)
