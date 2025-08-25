from app import db
from datetime import datetime

class Course(db.Model):
    """Represents a university course/major"""
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # e.g., 'MJD-FINEC'
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to units
    units = db.relationship('CourseUnit', back_populates='course', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Course {self.code}: {self.title}>'

class Unit(db.Model):
    """Represents a university unit"""
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)  # e.g., 'ECON1101'
    title = db.Column(db.String(200), nullable=False)
    credit_points = db.Column(db.Integer, default=6)
    
    # Raw prerequisite text from data source (for AI processing)
    prerequisites_raw = db.Column(db.Text)
    corequisites_raw = db.Column(db.Text)
    incompatibles_raw = db.Column(db.Text)
    
    # Additional metadata
    faculty = db.Column(db.String(100))
    availabilities_raw = db.Column(db.Text)  # Raw availability data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    course_units = db.relationship('CourseUnit', back_populates='unit')
    availabilities = db.relationship('UnitAvailability', back_populates='unit', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Unit {self.code}: {self.title}>'

class CourseUnit(db.Model):
    """Junction table linking courses to their required units"""
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    
    # Unit classification within the course
    unit_type = db.Column(db.String(20))  # 'core', 'option', 'elective', etc.
    year_level = db.Column(db.Integer)    # 1, 2, 3, 4
    sequence_order = db.Column(db.Integer)  # Order within sequence
    
    # Relationships
    course = db.relationship('Course', back_populates='units')
    unit = db.relationship('Unit', back_populates='course_units')
    
    def __repr__(self):
        return f'<CourseUnit {self.course.code} -> {self.unit.code}>'

class UnitAvailability(db.Model):
    """Tracks when units are available (semester/year)"""
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    
    year = db.Column(db.Integer, nullable=False)
    teaching_period = db.Column(db.String(50), nullable=False)  # 'Semester 1', 'Semester 2', etc.
    location = db.Column(db.String(50), default='Crawley')
    mode = db.Column(db.String(20), default='FACE2FACE')
    
    # Relationships
    unit = db.relationship('Unit', back_populates='availabilities')
    
    def __repr__(self):
        return f'<Availability {self.unit.code} {self.year} {self.teaching_period}>'

class StudyPlan(db.Model):
    """Represents a generated study plan (for future use if we add persistence)"""
    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('course.id'), nullable=False)
    plan_data = db.Column(db.JSON)  # Store the plan structure as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    course = db.relationship('Course')
    
    def __repr__(self):
        return f'<StudyPlan {self.course.code} created {self.created_at}>'