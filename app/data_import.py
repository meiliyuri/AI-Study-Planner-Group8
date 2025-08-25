import pandas as pd
import csv
from app import db
from app.models import Unit, Course, CourseUnit, UnitAvailability
import logging

logger = logging.getLogger(__name__)

class DataImporter:
    """Handles importing data from CSV/XLSX files into the database"""
    
    def import_units_csv(self, file_path):
        """Import units from the main Units.csv file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                units_created = 0
                
                for row in reader:
                    # Check if unit already exists
                    existing = Unit.query.filter_by(code=row['code']).first()
                    if existing:
                        continue
                    
                    unit = Unit(
                        code=row['code'],
                        title=row['title'],
                        prerequisites_raw=row.get('RulesPrereqs', ''),
                        corequisites_raw=row.get('RulesCoreqs', ''),
                        incompatibles_raw=row.get('RulesIncomps', ''),
                        availabilities_raw=row.get('Availabilities', ''),
                        credit_points=6  # Default, could be extracted from data
                    )
                    
                    db.session.add(unit)
                    units_created += 1
                
                db.session.commit()
                logger.info(f"Imported {units_created} units from {file_path}")
                return units_created
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error importing units CSV: {str(e)}")
            raise
    
    def import_unit_availabilities_csv(self, file_path):
        """Import unit availability data from Units Availabilities.csv"""
        try:
            availabilities_created = 0
            
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    unit_code = row.get('UnitCode', '').strip()
                    if not unit_code:
                        continue
                    
                    # Find the unit
                    unit = Unit.query.filter_by(code=unit_code).first()
                    if not unit:
                        continue
                    
                    # Check if availability already exists
                    existing = UnitAvailability.query.filter_by(
                        unit_id=unit.id,
                        year=int(row.get('Year', 0)),
                        teaching_period=row.get('TeachingPeriod', '')
                    ).first()
                    
                    if existing:
                        continue
                    
                    availability = UnitAvailability(
                        unit_id=unit.id,
                        year=int(row.get('Year', 2025)),
                        teaching_period=row.get('TeachingPeriod', ''),
                        location=row.get('Location', 'Crawley'),
                        mode=row.get('Mode', 'FACE2FACE')
                    )
                    
                    db.session.add(availability)
                    availabilities_created += 1
                
                db.session.commit()
                logger.info(f"Imported {availabilities_created} unit availabilities")
                return availabilities_created
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error importing unit availabilities: {str(e)}")
            raise
    
    def import_course_sequence_xlsx(self, file_path, course_code, course_title):
        """Import course sequence from XLSX file (MJD-FINEC, MJD-ECNPF)"""
        try:
            # Read the Excel file
            df = pd.read_excel(file_path)
            
            # Create or get the course
            course = Course.query.filter_by(code=course_code).first()
            if not course:
                course = Course(code=course_code, title=course_title)
                db.session.add(course)
                db.session.flush()  # Get the ID
            
            units_linked = 0
            
            # Process each row to extract unit codes
            for index, row in df.iterrows():
                # This will need to be adjusted based on actual XLSX structure
                # For now, assume there are columns with unit codes
                for col in df.columns:
                    cell_value = str(row[col]).strip()
                    
                    # Look for unit codes (pattern: 4 letters + 4 digits)
                    if self._looks_like_unit_code(cell_value):
                        unit = Unit.query.filter_by(code=cell_value).first()
                        if unit:
                            # Check if already linked
                            existing_link = CourseUnit.query.filter_by(
                                course_id=course.id,
                                unit_id=unit.id
                            ).first()
                            
                            if not existing_link:
                                course_unit = CourseUnit(
                                    course_id=course.id,
                                    unit_id=unit.id,
                                    unit_type='core',  # Default, could be inferred
                                    sequence_order=index
                                )
                                db.session.add(course_unit)
                                units_linked += 1
            
            db.session.commit()
            logger.info(f"Imported course {course_code} with {units_linked} units")
            return course, units_linked
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error importing course sequence: {str(e)}")
            raise
    
    def _looks_like_unit_code(self, text):
        """Check if text looks like a unit code (e.g., ECON1101)"""
        if not text or len(text) != 8:
            return False
        return text[:4].isalpha() and text[4:].isdigit()
    
    def get_import_status(self):
        """Get current database import status"""
        return {
            'units': Unit.query.count(),
            'courses': Course.query.count(), 
            'course_units': CourseUnit.query.count(),
            'availabilities': UnitAvailability.query.count()
        }

# Global importer instance
data_importer = DataImporter()