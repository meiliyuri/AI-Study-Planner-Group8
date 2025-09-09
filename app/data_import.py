# Data Import Service for loading university data from CSV files
# Written with the aid of Claude AI assistant
#
# This service handles importing and organizing university data:
#
# Main functions:
# 1. Import unit data from "Units with unit rules and availabilities.csv" 
# 2. Setup specific majors (Economics and Financial Economics)
# 3. Auto-discover majors from "Units.csv" curriculum data
# 4. Create degree programs for the web interface
#
# Data sources:
# - "Units with unit rules and availabilities.csv": All unit details, prerequisites, offerings
# - "Units.csv": Major mappings (which units belong to which majors as core/option)
#
# The system can automatically discover 165+ majors from the CSV data, but we only
# enable the ones we want to show to users. This keeps the interface clean while
# maintaining full scalability for future expansion.

import pandas as pd
import csv
import re
from app import db
from app.models import Unit, BachelorDegree, Major, MajorUnit, DegreeProgram, UnitAvailability
import logging

logger = logging.getLogger(__name__)

class DataImporter:
    """Handles importing data from the new comprehensive CSV format"""
    
    def import_comprehensive_units_csv(self, file_path):
        """Import units from the comprehensive 'Units with unit rules and availabilities.csv'"""
        try:
            units_created = 0
            units_updated = 0
            availabilities_created = 0
            
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    unit_code = row.get('unitnumber', '').strip()
                    if not unit_code:
                        continue
                    
                    # Check if unit already exists (update it with full data)
                    existing_unit = Unit.query.filter_by(code=unit_code).first()
                    if existing_unit:
                        # Update existing unit with comprehensive data
                        existing_unit.title = row.get('unitname', '') or existing_unit.title
                        existing_unit.credit_points = int(row.get('points', 6)) if row.get('points') and row.get('points').isdigit() else existing_unit.credit_points
                        existing_unit.prerequisites_raw = row.get('prereqs', '')
                        existing_unit.corequisites_raw = row.get('coreqs', '')
                        existing_unit.incompatibles_raw = row.get('incompatible', '')
                        existing_unit.faculty = row.get('faculty', '')
                        existing_unit.department = row.get('dept', '')
                        existing_unit.description = row.get('bodycopy', '')
                        existing_unit.unit_coordinator = row.get('unitcoord', '')
                        existing_unit.outcomes = row.get('outcomes', '')
                        existing_unit.assessment = row.get('ams', '')
                        existing_unit.offering_raw = row.get('offering', '')
                        existing_unit.study_type = row.get('studytype', '')
                        existing_unit.offer_mode = row.get('offermode', '')
                        
                        units_updated += 1
                        unit = existing_unit
                    else:
                        # Create new unit with comprehensive data
                        unit = Unit(
                            code=unit_code,
                            title=row.get('unitname', ''),
                            credit_points=int(row.get('points', 6)) if row.get('points') and row.get('points').isdigit() else 6,
                            prerequisites_raw=row.get('prereqs', ''),
                            corequisites_raw=row.get('coreqs', ''),
                            incompatibles_raw=row.get('incompatible', ''),
                            faculty=row.get('faculty', ''),
                            department=row.get('dept', ''),
                            description=row.get('bodycopy', ''),
                            unit_coordinator=row.get('unitcoord', ''),
                            outcomes=row.get('outcomes', ''),
                            assessment=row.get('ams', ''),
                            offering_raw=row.get('offering', ''),
                            study_type=row.get('studytype', ''),
                            offer_mode=row.get('offermode', '')
                        )
                        
                        db.session.add(unit)
                        db.session.flush()  # Get the unit ID
                        units_created += 1
                    
                    # Process availability data from offering field
                    availabilities_created += self._process_unit_offerings(
                        unit, row.get('offering', '')
                    )
                
                db.session.commit()
                
                result = {
                    'units_created': units_created,
                    'units_updated': units_updated,
                    'availabilities_created': availabilities_created
                }
                
                logger.info(f"Import complete: {result}")
                return result
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error importing comprehensive units CSV: {str(e)}")
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
    
    
    def _get_course_title_from_code(self, major_code):
        """Generate a readable course title from major code"""
        # Comprehensive mapping for course codes
        code_mappings = {
            # Business School Majors
            'MJD-ECNPF': 'Economics',
            'MJD-FINEC': 'Financial Economics', 
            'MJD-FINCE': 'Finance',
            'MJD-ACCTG': 'Accounting',
            'MJD-BUSAN': 'Business Analytics',
            'MJD-GLBUS': 'Global Business',
            'MJD-ECNSM': 'Economics and Management',
            'MJD-BSLAW': 'Business Law',
            'MJD-MGMT': 'Management',
            'MJD-MKTNG': 'Marketing',
            'MJD-STATS': 'Statistics',
            
            # Agriculture & Environment
            'MJD-AGBDM': 'Agricultural Business Development and Management',
            'MJD-AGBUS': 'Agribusiness',
            'MJD-AGSCI': 'Agricultural Science',
            'MJD-AGTDM': 'Agricultural Technology and Data Management',
            'MJD-AGTEC': 'Agricultural Technology',
            
            # Bachelor Programs (simplified)
            'BP001': 'Bachelor of Arts',
            'BP002': 'Bachelor of Commerce', 
            'BP004': 'Bachelor of Science',
            'BP006': 'Bachelor of Engineering',
            'BP007': 'Bachelor of Computer Science',
            'BP008': 'Bachelor of Medicine',
            'BP009': 'Bachelor of Dental Medicine',
            'BP011': 'Bachelor of Biomedical Science',
            'BP012': 'Bachelor of Exercise and Health',
            'BP013': 'Bachelor of Economics',
            'BP014': 'Bachelor of Philosophy (Honours)',
            'BP019': 'Bachelor of Psychology',
            'BP020': 'Bachelor of Design',
            
            # Bachelor Honours Programs
            'BH008': 'Bachelor of Medicine (Honours)',
            'BH011': 'Bachelor of Biomedical Science (Honours)', 
            'BH017': 'Bachelor of Psychology (Honours)',
            'BH020': 'Bachelor of Design (Honours)',
            'BH028': 'Bachelor of Exercise and Health (Honours)',
            'BH039': 'Bachelor of Computer Science (Honours)',
            
            # Combined Bachelor Programs
            'CB001': 'Bachelor of Arts / Bachelor of Commerce',
            'CB002': 'Bachelor of Arts / Bachelor of Science',
            'CB003': 'Bachelor of Commerce / Bachelor of Science',
            'CB004': 'Bachelor of Engineering / Bachelor of Commerce'
        }
        
        # If we have a specific mapping, use it
        if major_code in code_mappings:
            return code_mappings[major_code]
        
        # For unknown codes, try to make them readable
        if major_code.startswith('MJD-'):
            return major_code.replace('MJD-', '').replace('-', ' ').title()
        elif major_code.startswith('BP'):
            return f"Bachelor Program {major_code[2:]}"
        elif major_code.startswith('BH'):
            return f"Bachelor Honours {major_code[2:]}"
        elif major_code.startswith('CB'):
            return f"Combined Bachelor {major_code[2:]}"
        else:
            return major_code.replace('-', ' ').title()
    
    def _process_unit_offerings(self, unit, offering_str):
        """Parse the complex offering string and create UnitAvailability records"""
        if not offering_str:
            return 0
        
        availabilities_created = 0
        
        # Split multiple offerings by ~
        offerings = offering_str.split('~')
        
        for offering in offerings:
            if not offering.strip():
                continue
            
            # Parse format: "Semester 1|6|UWA (Perth)|Face to face"
            parts = offering.split('|')
            if len(parts) >= 4:
                teaching_period = parts[0].strip()
                location_raw = parts[2].strip()
                mode_raw = parts[3].strip()
                
                # Extract location (remove parentheses)
                location = re.sub(r'\(.*\)', '', location_raw).strip()
                if not location:
                    location = 'Perth'
                
                # Clean up mode
                mode = 'FACE2FACE' if 'face to face' in mode_raw.lower() else mode_raw.upper()
                
                # Check if availability already exists
                existing = UnitAvailability.query.filter_by(
                    unit_id=unit.id,
                    year=2025,  # Current year default
                    teaching_period=teaching_period
                ).first()
                
                if not existing:
                    availability = UnitAvailability(
                        unit_id=unit.id,
                        year=2025,
                        teaching_period=teaching_period,
                        location=location,
                        mode=mode
                    )
                    
                    db.session.add(availability)
                    availabilities_created += 1
        
        return availabilities_created
    
    def _looks_like_unit_code(self, text):
        """Check if text looks like a unit code (e.g., ECON1101)"""
        if not text or len(text) != 8:
            return False
        return text[:4].isalpha() and text[4:].isdigit()
    
    def _is_broad_bachelor_program(self, course_code):
        """Check if course code represents a broad bachelor program
        
        These programs represent general elective availability rather than 
        structured degree sequences and should be excluded from electives processing.
        """
        # BP* = Bachelor Programs (e.g., BP004 = Bachelor of Science)
        # BH* = Bachelor Honours Programs 
        # CB* = Combined Bachelor Programs
        return course_code.startswith(('BP', 'BH', 'CB'))
    
    def setup_specific_majors(self):
        """Set up the two specific majors: MJD-ECNPF and MJD-FINEC"""
        try:
            # Create Bachelor of Economics degree
            bachelor_econ = BachelorDegree.query.filter_by(code='BEC').first()
            if not bachelor_econ:
                bachelor_econ = BachelorDegree(
                    code='BEC',
                    title='Bachelor of Economics',
                    total_credit_points=144,
                    duration_years=3,
                    description='A 3-year full-time degree focusing on economic analysis and policy'
                )
                db.session.add(bachelor_econ)
                db.session.flush()
            
            # Create Economics Major (MJD-ECNPF)
            major_ecnpf = Major.query.filter_by(code='MJD-ECNPF').first()
            if not major_ecnpf:
                major_ecnpf = Major(
                    code='MJD-ECNPF',
                    title='Economics',
                    bachelor_degree_id=bachelor_econ.id,
                    description='Major in Economics focusing on microeconomic and macroeconomic theory and applications'
                )
                db.session.add(major_ecnpf)
                db.session.flush()
            
            # Create Financial Economics Major (MJD-FINEC)
            major_finec = Major.query.filter_by(code='MJD-FINEC').first()
            if not major_finec:
                major_finec = Major(
                    code='MJD-FINEC',
                    title='Financial Economics',
                    bachelor_degree_id=bachelor_econ.id,
                    description='Major in Financial Economics combining economics with finance theory and practice'
                )
                db.session.add(major_finec)
                db.session.flush()
            
            # Create degree programs
            self._create_degree_program(bachelor_econ, major_ecnpf, 'BEC-ECNPF', 
                                       'Bachelor of Economics, Major in Economics')
            self._create_degree_program(bachelor_econ, major_finec, 'BEC-FINEC', 
                                       'Bachelor of Economics, Major in Financial Economics')
            
            # Set up major requirements
            self._setup_ecnpf_requirements(major_ecnpf)
            self._setup_finec_requirements(major_finec)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Successfully set up MJD-ECNPF and MJD-FINEC majors'
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error setting up specific majors: {str(e)}")
            raise
    
    def _create_degree_program(self, bachelor_degree, major, code, display_title):
        """Create a degree program if it doesn't exist"""
        existing = DegreeProgram.query.filter_by(
            bachelor_degree_id=bachelor_degree.id,
            major_id=major.id
        ).first()
        
        if not existing:
            degree_program = DegreeProgram(
                bachelor_degree_id=bachelor_degree.id,
                major_id=major.id,
                code=code,
                display_title=display_title,
                is_active=True
            )
            db.session.add(degree_program)
    
    def _setup_ecnpf_requirements(self, major):
        """Set up MJD-ECNPF (Economics) major requirements"""
        # Level 1 Core (24 points) - Take all units
        level1_core = [
            'ECON1101', 'ECON1102', 'FINA1221', 'STAT1520'
        ]
        
        # Level 2 Core (24 points) - Take all units
        level2_core = [
            'ECON2233', 'ECON2234', 'ECON2271', 'ECON2272'
        ]
        
        # Level 2 Options (6 points) - Take unit(s) to the value of 6 points
        level2_options = [
            'ECON2105', 'ECON2106', 'ECON2210', 'ECON2245', 'FINA2205'
        ]
        
        # Level 3 Core (18 points) - Take all units
        level3_core = [
            'ECON3302', 'ECON3303', 'ECON3371'
        ]
        
        # Level 3 Options (18 points) - Take unit(s) to the value of 18 points
        level3_options = [
            'ECON3205', 'ECON3206', 'ECON3220', 'ECON3235', 'ECON3236',
            'ECON3301', 'ECON3310', 'ECON3350', 'ECON3395', 'WILG3001'
        ]
        
        self._add_units_to_major(major, level1_core, 'core', 1, True)
        self._add_units_to_major(major, level2_core, 'core', 2, True)
        self._add_units_to_major(major, level2_options, 'option', 2, False)
        self._add_units_to_major(major, level3_core, 'core', 3, True)
        self._add_units_to_major(major, level3_options, 'option', 3, False)
    
    def _setup_finec_requirements(self, major):
        """Set up MJD-FINEC (Financial Economics) major requirements"""
        # Level 1 Core (24 points)
        level1_core = [
            'ECON1101', 'ECON1102', 'FINA1221', 'STAT1520'
        ]
        
        # Level 2 Core (30 points)
        level2_core = [
            'ECON2233', 'ECON2234', 'ECON2271', 'ECON2272', 'FINA2222'
        ]
        
        # Level 3 Core (24 points)
        level3_core = [
            'ECON3236', 'ECON3350', 'ECON3371', 'FINA3324'
        ]
        
        # Level 3 Options (12 points)
        level3_options = [
            'ECON3235', 'ECON3301', 'ECON3302', 'ECON3303', 'FINA3304',
            'FINA3307', 'FINA3326', 'WILG3001'
        ]
        
        self._add_units_to_major(major, level1_core, 'core', 1, True)
        self._add_units_to_major(major, level2_core, 'core', 2, True)
        self._add_units_to_major(major, level3_core, 'core', 3, True)
        self._add_units_to_major(major, level3_options, 'option', 3, False)
    
    def _add_units_to_major(self, major, unit_codes, unit_type, year_level, is_mandatory):
        """Add units to a major with the specified parameters"""
        for unit_code in unit_codes:
            # Find or create unit
            unit = Unit.query.filter_by(code=unit_code).first()
            if not unit:
                # Create a basic unit record if it doesn't exist
                unit = Unit(
                    code=unit_code,
                    title=f"Unit {unit_code}",  # Will be updated from CSV import
                    credit_points=6
                )
                db.session.add(unit)
                db.session.flush()
            
            # Check if major-unit relationship already exists
            existing = MajorUnit.query.filter_by(
                major_id=major.id,
                unit_id=unit.id
            ).first()
            
            if not existing:
                major_unit = MajorUnit(
                    major_id=major.id,
                    unit_id=unit.id,
                    unit_type=unit_type,
                    year_level=year_level,
                    is_mandatory=is_mandatory
                )
                db.session.add(major_unit)
    
    def discover_major_mappings_from_csv(self, units_csv_path):
        """
        Auto-discover major mappings from Units.csv curriculum data
        Returns dict of major_code -> {core: [], option: [], bridging: []}
        """
        import csv
        import re
        
        major_mappings = {}
        
        try:
            with open(units_csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    code = row['code']
                    curriculum = row.get('Curriculum', '')
                    
                    # Find all major references in curriculum
                    major_matches = re.findall(r'MJD-[A-Z]{5}', curriculum)
                    
                    for major_code in major_matches:
                        if major_code not in major_mappings:
                            major_mappings[major_code] = {
                                'core': [],
                                'option': [],
                                'bridging': []
                            }
                        
                        # Check unit classification
                        major_section = curriculum.split(major_code)[1].split(';')[0] if major_code in curriculum else ''
                        
                        if ' as core ' in major_section and '[Active]' in major_section:
                            major_mappings[major_code]['core'].append(code)
                        elif ' as option ' in major_section and '[Active]' in major_section:
                            major_mappings[major_code]['option'].append(code)
                        elif ' as bridging ' in major_section and '[Active]' in major_section:
                            major_mappings[major_code]['bridging'].append(code)
            
            return major_mappings
            
        except Exception as e:
            print(f"Error discovering major mappings: {e}")
            return {}
    
    def create_major_from_discovery(self, major_code, units_data, enabled=False):
        """
        Create a major and its requirements from discovered units data
        units_data should be in format: {core: [], option: [], bridging: []}
        """
        try:
            # Get or create bachelor degree (assuming Bachelor of Economics for now)
            bachelor_degree = BachelorDegree.query.filter_by(code='BEC').first()
            if not bachelor_degree:
                bachelor_degree = BachelorDegree(
                    code='BEC',
                    title='Bachelor of Economics',
                    duration_years=3,
                    total_credit_points=144
                )
                db.session.add(bachelor_degree)
                db.session.flush()
            
            # Create major
            major_title = self._get_course_title_from_code(major_code)
            major = Major(
                code=major_code,
                title=major_title,
                bachelor_degree_id=bachelor_degree.id,
                is_active=enabled
            )
            db.session.add(major)
            db.session.flush()
            
            # Add core units
            if units_data.get('core'):
                self._add_discovered_units_to_major(major, units_data['core'], 'core', is_mandatory=True)
            
            # Add option units  
            if units_data.get('option'):
                self._add_discovered_units_to_major(major, units_data['option'], 'option', is_mandatory=False)
            
            # Add bridging units (treat as option for now)
            if units_data.get('bridging'):
                self._add_discovered_units_to_major(major, units_data['bridging'], 'option', is_mandatory=False)
            
            db.session.commit()
            
            return major
            
        except Exception as e:
            db.session.rollback()
            print(f"Error creating major {major_code}: {e}")
            return None
    
    def _add_discovered_units_to_major(self, major, unit_codes, unit_type, is_mandatory):
        """Add discovered units to major with automatic year level detection"""
        for unit_code in unit_codes:
            unit = Unit.query.filter_by(code=unit_code).first()
            if unit:
                # Detect year level from unit code (ECON1101 = level 1, ECON2233 = level 2, etc.)
                year_level = 1
                if len(unit_code) >= 4 and unit_code[4].isdigit():
                    year_level = int(unit_code[4])
                
                major_unit = MajorUnit(
                    major_id=major.id,
                    unit_id=unit.id,
                    unit_type=unit_type,
                    year_level=year_level,
                    is_mandatory=is_mandatory
                )
                db.session.add(major_unit)
    
    def get_import_status(self):
        """Get current database import status"""
        return {
            'units': Unit.query.count(),
            'bachelor_degrees': BachelorDegree.query.count(), 
            'majors': Major.query.count(),
            'degree_programs': DegreeProgram.query.count(),
            'major_units': MajorUnit.query.count(),
            'availabilities': UnitAvailability.query.count()
        }

# Global importer instance
data_importer = DataImporter()