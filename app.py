# Main Flask application entry point
# Written with the aid of Claude AI assistant
#
# This file starts the AI Study Planner Flask web application.
# To run the app: python app.py or python -m flask run
#
# The app helps university students plan their degree by:
# 1. Showing available degree programs (Economics, Financial Economics)
# 2. Generating AI-powered study plans (6 semesters, 24 units)
# 3. Allowing drag-and-drop customization with prerequisite validation
# 4. Exporting study plans to PDF format

from app import create_app, db
from app.models import Unit, BachelorDegree, Major, DegreeProgram, MajorUnit, UnitAvailability

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db, 
        'Unit': Unit, 
        'BachelorDegree': BachelorDegree,
        'Major': Major,
        'DegreeProgram': DegreeProgram,
        'MajorUnit': MajorUnit,
        'UnitAvailability': UnitAvailability
    }

if __name__ == '__main__':
    app.run(debug=True)