# Route definitions for AI Study Planner application
# Separates URL routing from business logic (kept in controller.py)
# Written following the pattern from Miguel's Flask tutorial, adapted for academic planning

from app import app  # Flask application instance
from flask import render_template, request, jsonify, session  # Flask routing and request functions
from app import controller  # Controller functions for business logic
import uuid  # UUID generation for session management

@app.route('/')  # Root URL route
def index():
    """Homepage for AI Study Planner

    Shows available degree programs in an attractive layout.

    Returns:
        HTML template: Homepage with degree program selection
    """
    return render_template('home.html', title_page="AI Study Planner")

@app.route('/planner')  # Study planner interface
def planner():
    """Study planner interface for AI Study Planner

    Generates a unique session ID for user tracking and renders
    the main application interface. Optionally pre-selects a major
    if specified in query parameters.

    Returns:
        HTML template: Study planner application page
    """
    # Generate a session ID if not exists - Flask session function
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())  # Generate unique identifier

    # Get pre-selected major from query parameters
    selected_major = request.args.get('major', '')

    return render_template('planner.html', title_page="Study Planner", selected_major=selected_major)

@app.route('/api/majors', methods=['GET'])  # API endpoint for major data
def get_majors():
    """API endpoint to retrieve available academic majors

    Returns JSON list of all available majors for frontend selection.

    Returns:
        JSON response: List of majors with details
    """
    return controller.get_available_majors()  # Delegate to controller function

@app.route('/api/generate_plan', methods=['POST'])  # API endpoint for plan generation
def generate_plan():
    """API endpoint to generate initial study plan

    Uses Claude AI to create a comprehensive 3-year study plan
    based on selected major and UWA degree requirements.

    Returns:
        JSON response: Complete study plan with unit details
    """
    return controller.generate_initial_plan()  # Delegate to controller function

@app.route('/api/validate_plan', methods=['POST'])
def validate_plan():
    return controller.validate_study_plan()

@app.route('/api/units', methods=['GET'])
def get_units():
    return controller.get_available_units()

@app.route('/api/export_pdf', methods=['POST'])
def export_pdf():
    return controller.export_plan_to_pdf()

@app.route('/api/ai_validate_plan', methods=['POST'])
def ai_validate_plan():
    return controller.ai_validate_plan()

@app.route('/admin')
def admin():
    return render_template('admin.html', title_page="Admin Panel")

@app.route('/contact')
def contact():
    return render_template('contact.html', title_page="Contact Us")

@app.route('/faq')
def faq():
    return render_template('faq.html', title_page="FAQ's")

@app.route('/api/admin/import_data', methods=['POST'])
def import_data():
    return controller.import_course_data()

@app.route('/api/admin/clear_cache', methods=['POST'])
def clear_cache():
    return controller.clear_plan_cache()