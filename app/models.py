# Database models for AI Study Planner application
# Defines the database schema for academic units, majors, and study plans
# Written using SQLAlchemy ORM following Flask patterns

from datetime import datetime  # Date and time utilities for timestamps
from app import db  # SQLAlchemy database instance

class Unit(db.Model):
    """Academic unit model representing individual courses

    Stores information about university units including prerequisites,
    availability, and academic level. Used for study plan generation.
    """
    # Primary key and unique identifier
    id = db.Column(db.Integer, primary_key=True)

    # Unit identification - SQLAlchemy indexed for performance
    code = db.Column(db.String(10), unique=True, nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)

    # Academic level (1, 2, or 3) for progression rules
    level = db.Column(db.Integer, nullable=False)

    # Credit points (typically 6 for UWA units)
    points = db.Column(db.Integer, default=6)

    # Academic constraint information stored as text
    availabilities = db.Column(db.Text)  # Semester availability information
    prerequisites = db.Column(db.Text)   # Required units before this one
    corequisites = db.Column(db.Text)    # Units to be taken simultaneously
    incompatibilities = db.Column(db.Text)  # Units that cannot be taken together

    # Special unit classification
    is_bridging = db.Column(db.Boolean, default=False)  # Bridging unit flag

    def __repr__(self):
        """String representation of Unit object for debugging"""
        return f'<Unit {self.code}: {self.title}>'

    def get_level_from_code(self):
        """Extract academic level from unit code

        UWA unit codes follow format: ABCD1234 where 1 indicates level.

        Returns:
            int: Academic level (1, 2, or 3), defaults to 1 if cannot parse
        """
        if len(self.code) >= 5:  # Check if code is long enough
            return int(self.code[4])  # Fifth character indicates level
        return 1  # Default to level 1 if code format is unexpected

class Major(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    degree = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Major {self.code}: {self.name}>'

class MajorUnit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    major_id = db.Column(db.Integer, db.ForeignKey('major.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('unit.id'), nullable=False)
    requirement_type = db.Column(db.String(20), nullable=False)  # 'core', 'option', 'bridging'
    level = db.Column(db.Integer, nullable=False)

    major = db.relationship('Major', backref='major_units')
    unit = db.relationship('Unit', backref='major_units')

    def __repr__(self):
        return f'<MajorUnit {self.major.code} - {self.unit.code} ({self.requirement_type})>'

class StudyPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(100), nullable=False, index=True)
    major_id = db.Column(db.Integer, db.ForeignKey('major.id'), nullable=False)
    plan_data = db.Column(db.Text)  # JSON string of the plan
    is_valid = db.Column(db.Boolean, default=False)
    validation_errors = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    major = db.relationship('Major', backref='study_plans')

    def __repr__(self):
        return f'<StudyPlan {self.session_id} - {self.major.code}>'