from app import create_app, db
from app.models import Unit, Course, UnitAvailability

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Unit': Unit, 'Course': Course, 'UnitAvailability': UnitAvailability}

if __name__ == '__main__':
    app.run(debug=True)