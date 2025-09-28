import pandas as pd
import os
from app import app, db
from app.models import Unit, Major, MajorUnit

# List of bridging units to exclude
BRIDGING_UNITS = ['CHEM1003', 'MATH1720', 'SCIE1500', 'ECON1111']

def load_units_csv():
    """Load units from Units.csv"""
    csv_path = 'Reference_Material/Essential_Data/Units.csv'

    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    print("Loading units from Units.csv...")
    df = pd.read_csv(csv_path)

    loaded_count = 0
    for _, row in df.iterrows():
        unit_code = row['code']
        unit_title = row['title']

        # Skip rows with missing essential data
        if pd.isna(unit_code) or pd.isna(unit_title) or str(unit_code).strip() == '' or str(unit_title).strip() == '':
            continue

        # Clean the data
        unit_code = str(unit_code).strip()
        unit_title = str(unit_title).strip()

        # Extract level from unit code (5th character)
        level = 1
        if len(unit_code) >= 5:
            try:
                level = int(unit_code[4])
            except (ValueError, IndexError):
                level = 1

        # Check if it's a bridging unit
        is_bridging = unit_code in BRIDGING_UNITS

        # Check if unit already exists
        existing_unit = Unit.query.filter_by(code=unit_code).first()
        if not existing_unit:
            unit = Unit(
                code=unit_code,
                title=unit_title,
                level=level,
                points=6,  # Default 6 points
                is_bridging=is_bridging
            )
            db.session.add(unit)
            loaded_count += 1

    db.session.commit()
    print(f"Loaded {loaded_count} valid units from Units.csv")

def load_units_with_rules_csv():
    """Load unit rules from Units with unit rules and availabilities.csv"""
    csv_path = 'Reference_Material/Essential_Data/Units with unit rules and availabilities.csv'

    if not os.path.exists(csv_path):
        print(f"File not found: {csv_path}")
        return

    print("Loading unit rules from Units with unit rules and availabilities.csv...")
    df = pd.read_csv(csv_path)

    def clean_field(value):
        """Clean field value, converting nan to empty string"""
        if pd.isna(value) or str(value).lower() == 'nan':
            return ''
        return str(value).strip()

    updated_count = 0
    for _, row in df.iterrows():
        unit_code = row['unitnumber']
        unit_title = row['unitname']

        # Skip rows with missing essential data
        if pd.isna(unit_code) or pd.isna(unit_title) or str(unit_code).strip() == '' or str(unit_title).strip() == '':
            continue

        # Clean the data
        unit_code = str(unit_code).strip()
        unit_title = str(unit_title).strip()

        # Extract level from unit code
        level = 1
        if len(unit_code) >= 5:
            try:
                level = int(unit_code[4])
            except (ValueError, IndexError):
                level = 1

        # Get availability, prerequisites, etc. - clean the fields
        availabilities = clean_field(row.get('offering', ''))
        prerequisites = clean_field(row.get('prereqs', ''))
        corequisites = clean_field(row.get('coreqs', ''))
        incompatibilities = clean_field(row.get('incompatible', ''))
        electives = clean_field(row.get('electives', ''))

        # Check if it's a bridging unit
        is_bridging = unit_code in BRIDGING_UNITS

        # Update existing unit or create new one
        unit = Unit.query.filter_by(code=unit_code).first()
        if unit:
            unit.availabilities = availabilities
            unit.prerequisites = prerequisites
            unit.corequisites = corequisites
            unit.incompatibilities = incompatibilities
            unit.electives = electives
            unit.is_bridging = is_bridging
            updated_count += 1
        else:
            unit = Unit(
                code=unit_code,
                title=unit_title,
                level=level,
                points=6,
                availabilities=availabilities,
                prerequisites=prerequisites,
                corequisites=corequisites,
                incompatibilities=incompatibilities,
                electives=electives,
                is_bridging=is_bridging
            )
            db.session.add(unit)
            updated_count += 1

    db.session.commit()
    print(f"Updated {updated_count} valid units with rules and availability data")

def load_major_sequence_xlsx(file_path, major_code, major_name, degree, course_code):
    """Load major sequence from XLSX file"""
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    print(f"Loading major sequence: {major_code} from {file_path}")

    try:
        # Read the XLSX file - skip first 2 rows (metadata), use row 2 as headers
        df = pd.read_excel(file_path, sheet_name='Sequence export', skiprows=2, header=0)


        # Create or get major
        major = Major.query.filter_by(code=major_code).first()
        if not major:
            major = Major(code=major_code, name=major_name, degree=degree, course_code=course_code)
            db.session.add(major)
            db.session.flush()  # Get the ID

        # Process each row in the sequence
        for _, row in df.iterrows():
            unit_code = row.get('Code', '')
            curriculum = str(row.get('Curriculum', ''))

            if not unit_code or pd.isna(unit_code):
                continue

            # Clean the unit code
            unit_code = str(unit_code).strip()

            # Find the unit
            unit = Unit.query.filter_by(code=unit_code).first()
            if not unit:
                print(f"Warning: Unit {unit_code} not found in database")
                continue


            # Determine requirement type from curriculum column
            requirement_type = 'option'  # default
            if f'{major_code}' in curriculum and 'as core' in curriculum:
                requirement_type = 'core'
            elif f'{major_code}' in curriculum and 'as option' in curriculum:
                requirement_type = 'option'
            elif f'{major_code}' in curriculum and 'as bridging' in curriculum:
                requirement_type = 'bridging'
            else:
                continue  # Skip if not related to this major

            # Check if relationship already exists
            existing = MajorUnit.query.filter_by(
                major_id=major.id,
                unit_id=unit.id
            ).first()

            if not existing:
                major_unit = MajorUnit(
                    major_id=major.id,
                    unit_id=unit.id,
                    requirement_type=requirement_type,
                    level=unit.level
                )
                db.session.add(major_unit)

        db.session.commit()
        print(f"Loaded major {major_code} successfully")

    except Exception as e:
        print(f"Error loading {file_path}: {str(e)}")
        db.session.rollback()

def load_all_majors():
    """Load all major sequence files"""
    major_files = [
        ('Reference_Material/Essential_Data/Sequence export (MJD-ECNPF).xlsx', 'MJD-ECNPF', 'Economics', 'Bachelor of Economics', 'BP013'),
        ('Reference_Material/Essential_Data/Sequence export (MJD-FINEC).xlsx', 'MJD-FINEC', 'Financial Economics', 'Bachelor of Economics', 'BP013'),
        ('Reference_Material/Essential_Data/Sequence export MJD-AGBUS.xlsx', 'MJD-AGBUS', 'Agribusiness', 'Bachelor of Science', 'BP004'),
        ('Reference_Material/Essential_Data/Sequence export MJD-AGSCI.xlsx', 'MJD-AGSCI', 'Agricultural Science', 'Bachelor of Science', 'BP004'),
        ('Reference_Material/Essential_Data/Sequence export MJD-AGTEC.xlsx', 'MJD-AGTEC', 'Agricultural Technology', 'Bachelor of Science', 'BP004'),
    ]

    for file_path, major_code, major_name, degree, course_code in major_files:
        load_major_sequence_xlsx(file_path, major_code, major_name, degree, course_code)

def initialize_database():
    """Initialize the database with all course data"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()

        print("Loading course data...")
        load_units_csv()
        load_units_with_rules_csv()
        load_all_majors()

        print("Database initialization complete!")

        # Print summary
        unit_count = Unit.query.count()
        major_count = Major.query.count()
        major_unit_count = MajorUnit.query.count()

        print(f"\nSummary:")
        print(f"- Units: {unit_count}")
        print(f"- Majors: {major_count}")
        print(f"- Major-Unit relationships: {major_unit_count}")

if __name__ == '__main__':
    initialize_database()