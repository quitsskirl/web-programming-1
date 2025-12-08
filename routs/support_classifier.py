from flask import Blueprint, render_template

# Blueprint name 'classifier' – used in url_for('classifier.support_classifier_page')
classifier_bp = Blueprint('classifier', __name__)


@classifier_bp.route('/support-classifier')
def support_classifier_page():
    """
    Display the Student Support Classifier tool.

    URL: http://localhost:5000/support-classifier

    The page hosts a UI that calls the Flask /api/classify endpoint.
    """
    return render_template('SupportClassifier.html')
