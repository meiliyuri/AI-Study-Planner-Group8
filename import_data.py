#!/usr/bin/env python3
"""
Data Import Script for AI Study Planner
Imports course and unit data from CSV/XLSX files
"""

import sys
import os
from app import create_app, db
from app.data_import import data_importer
from app.models import Course

def main():
    """Main import function"""
    app = create_app()
    
    with app.app_context():
        print("AI Study Planner - Data Import")
        print("=" * 40)
        
        # Create database tables
        print("Creating database tables...")
        db.create_all()
        print("✓ Database tables created")
        
        # Import Units.csv
        units_file = "Reference_Material/Data_from_Client/Units.csv"
        if os.path.exists(units_file):
            print(f"\nImporting units from {units_file}...")
            try:
                count = data_importer.import_units_csv(units_file)
                print(f"✓ Imported {count} units")
            except Exception as e:
                print(f"✗ Error importing units: {e}")
        else:
            print(f"✗ Units file not found: {units_file}")
        
        # Import Unit Availabilities
        availability_file = "Reference_Material/Data_from_Client/Units Availabilities.csv"
        if os.path.exists(availability_file):
            print(f"\nImporting unit availabilities from {availability_file}...")
            try:
                count = data_importer.import_unit_availabilities_csv(availability_file)
                print(f"✓ Imported {count} unit availabilities")
            except Exception as e:
                print(f"✗ Error importing availabilities: {e}")
        else:
            print(f"✗ Availabilities file not found: {availability_file}")
        
        # Import course sequences
        courses_to_import = [
            {
                'file': 'Reference_Material/Data_from_Client/Sequence export (MJD-FINEC).xlsx',
                'code': 'MJD-FINEC', 
                'title': 'Financial Economics'
            },
            {
                'file': 'Reference_Material/Data_from_Client/Sequence export (MJD-ECNPF).xlsx',
                'code': 'MJD-ECNPF',
                'title': 'Economics'
            }
        ]
        
        for course_info in courses_to_import:
            file_path = course_info['file']
            if os.path.exists(file_path):
                print(f"\nImporting course {course_info['code']} from {file_path}...")
                try:
                    course, unit_count = data_importer.import_course_sequence_xlsx(
                        file_path, 
                        course_info['code'], 
                        course_info['title']
                    )
                    print(f"✓ Imported course {course.code} with {unit_count} units")
                except Exception as e:
                    print(f"✗ Error importing course {course_info['code']}: {e}")
            else:
                print(f"✗ Course file not found: {file_path}")
        
        # Show final status
        print("\n" + "=" * 40)
        print("Import Summary:")
        status = data_importer.get_import_status()
        for key, value in status.items():
            print(f"  {key.title()}: {value}")
        
        print("\n✓ Data import completed!")
        print("\nYou can now run the application with:")
        print("  python3 app.py")

if __name__ == '__main__':
    main()