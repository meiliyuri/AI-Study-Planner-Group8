# Database models for the AI Study Planner Flask application
# Written with the aid of Claude AI assistant
#
# This file defines the database structure for storing university study plan data:
# - BachelorDegree: Degree programs like "Bachelor of Economics" 
# - Major: Specializations within degrees like "Economics" or "Financial Economics"
# - DegreeProgram: Complete programs combining degree + major (what users see)
# - Unit: Individual subjects/courses like "ECON1101 Microeconomics"
# - MajorUnit: Links majors to their required/optional units
# - UnitAvailability: When units are offered (Semester 1, Semester 2, etc.)
#
# Data flow: BachelorDegree -> Major -> MajorUnit -> Unit
# Example: Bachelor of Economics -> Major in Economics -> ECON1101 (core unit)

from app import db
from datetime import datetime

class BachelorDegree(db.Model):
    """Represents a Bachelor's degree program (e.g., Bachelor of Economics)"""
    __tablename__ = 'bachelor_degrees'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), unique=True, nullable=False)  # e.g., 'BEC'
    title = db.Column(db.String(200), nullable=False)  # e.g., 'Bachelor of Economics'
    total_credit_points = db.Column(db.Integer, default=144)  # Total points required
    duration_years = db.Column(db.Integer, default=3)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    majors = db.relationship('Major', back_populates='bachelor_degree', cascade='all, delete-orphan')
    degree_programs = db.relationship('DegreeProgram', back_populates='bachelor_degree')
    
    def __repr__(self):
        return f'<BachelorDegree {self.code}: {self.title}>'

class Major(db.Model):
    """Represents a major/specialization within a bachelor degree"""
    __tablename__ = 'majors'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(20), nullable=False)  # e.g., 'MJD-FINEC'
    title = db.Column(db.String(200), nullable=False)  # e.g., 'Financial Economics'
    bachelor_degree_id = db.Column(db.Integer, db.ForeignKey('bachelor_degrees.id'), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bachelor_degree = db.relationship('BachelorDegree', back_populates='majors')
    major_units = db.relationship('MajorUnit', back_populates='major', cascade='all, delete-orphan')
    degree_programs = db.relationship('DegreeProgram', back_populates='major')
    
    def __repr__(self):
        return f'<Major {self.code}: {self.title}>'

class DegreeProgram(db.Model):
    """Represents a complete degree program (Bachelor + Major combination)"""
    __tablename__ = 'degree_programs'
    
    id = db.Column(db.Integer, primary_key=True)
    bachelor_degree_id = db.Column(db.Integer, db.ForeignKey('bachelor_degrees.id'), nullable=False)
    major_id = db.Column(db.Integer, db.ForeignKey('majors.id'), nullable=False)
    
    # Display information
    display_title = db.Column(db.String(300))  # e.g., "Bachelor of Economics, Major in Financial Economics"
    code = db.Column(db.String(50))  # e.g., "BEC-FINEC"
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    bachelor_degree = db.relationship('BachelorDegree', back_populates='degree_programs')
    major = db.relationship('Major', back_populates='degree_programs')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('bachelor_degree_id', 'major_id', name='unique_degree_major'),)
    
    def __repr__(self):
        return f'<DegreeProgram {self.code}: {self.display_title}>'

class Unit(db.Model):
    """Represents a university unit"""
    __tablename__ = 'units'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False)  # e.g., 'ECON1101'
    title = db.Column(db.String(200), nullable=False)
    credit_points = db.Column(db.Integer, default=6)
    
    # Raw prerequisite text from data source
    prerequisites_raw = db.Column(db.Text)
    corequisites_raw = db.Column(db.Text)
    incompatibles_raw = db.Column(db.Text)
    
    # Additional metadata
    faculty = db.Column(db.String(100))
    department = db.Column(db.String(100))
    description = db.Column(db.Text)
    unit_coordinator = db.Column(db.String(200))
    outcomes = db.Column(db.Text)
    assessment = db.Column(db.Text)
    offering_raw = db.Column(db.Text)
    study_type = db.Column(db.String(50))
    offer_mode = db.Column(db.String(50))
    availabilities_raw = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    major_units = db.relationship('MajorUnit', back_populates='unit')
    availabilities = db.relationship('UnitAvailability', back_populates='unit', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Unit {self.code}: {self.title}>'

class MajorUnit(db.Model):
    """Junction table linking majors to their units with classification"""
    __tablename__ = 'major_units'
    
    id = db.Column(db.Integer, primary_key=True)
    major_id = db.Column(db.Integer, db.ForeignKey('majors.id'), nullable=False)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    
    # Unit classification within the major
    unit_type = db.Column(db.String(20), nullable=False)  # 'core', 'option', 'elective'
    year_level = db.Column(db.Integer)  # 1, 2, 3, 4
    semester_preference = db.Column(db.Integer)  # 1 or 2 (preferred semester)
    sequence_order = db.Column(db.Integer)  # Order within the major
    is_mandatory = db.Column(db.Boolean, default=False)  # True for core units
    
    # Relationships
    major = db.relationship('Major', back_populates='major_units')
    unit = db.relationship('Unit', back_populates='major_units')
    
    # Unique constraint
    __table_args__ = (db.UniqueConstraint('major_id', 'unit_id', name='unique_major_unit'),)
    
    def __repr__(self):
        return f'<MajorUnit {self.major.code} -> {self.unit.code} ({self.unit_type})>'

class UnitAvailability(db.Model):
    """Tracks when units are available (semester/year)"""
    __tablename__ = 'unit_availabilities'
    
    id = db.Column(db.Integer, primary_key=True)
    unit_id = db.Column(db.Integer, db.ForeignKey('units.id'), nullable=False)
    
    year = db.Column(db.Integer, nullable=False)
    teaching_period = db.Column(db.String(50), nullable=False)  # 'Semester 1', 'Semester 2', etc.
    location = db.Column(db.String(50), default='Crawley')
    mode = db.Column(db.String(20), default='FACE2FACE')
    
    # Relationships
    unit = db.relationship('Unit', back_populates='availabilities')
    
    def __repr__(self):
        return f'<Availability {self.unit.code} {self.year} {self.teaching_period}>'

class StudyPlan(db.Model):
    """Represents a generated study plan"""
    __tablename__ = 'study_plans'
    
    id = db.Column(db.Integer, primary_key=True)
    degree_program_id = db.Column(db.Integer, db.ForeignKey('degree_programs.id'), nullable=False)
    plan_data = db.Column(db.JSON)  # Store the plan structure as JSON
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    degree_program = db.relationship('DegreeProgram')
    
    def __repr__(self):
        return f'<StudyPlan {self.degree_program.code} created {self.created_at}>'