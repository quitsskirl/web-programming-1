from flask import Blueprint, render_template

# Create a Blueprint named 'resources'
# Used in templates as: url_for('resources.resources_page')
resources_bp = Blueprint('resources', __name__)


@resources_bp.route('/resources')
def resources_page():
    """
    Display the Resources page for students.
    
    URL: http://localhost:5000/resources
    
    This page provides mental health resources including:
    - Articles and guides
    - PDF documents
    - Helpful links
    - Videos and tutorials
    
    Resources will be added later.
    
    Returns:
        Rendered Resources.html template
    """
    return render_template('Resources.html')

