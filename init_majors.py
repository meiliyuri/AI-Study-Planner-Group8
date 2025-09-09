#!/usr/bin/env python3
# Database initialization script for AI Study Planner
# Written with the aid of Claude AI assistant
#
# This script sets up the database with the initial data needed to run the app:
# 1. Creates all database tables (if they don't exist)
# 2. Sets up the two majors we support: Economics (MJD-ECNPF) and Financial Economics (MJD-FINEC) 
# 3. Imports all unit data from the CSV file (3,000+ units with prerequisites)
# 4. Shows a summary of what was imported
#
# Run this once after cloning the project: python init_majors.py

from app import create_app, db
from app.data_import import data_importer
import os

def init_database():
    """Initialize the database with the required data"""
    app = create_app()
    
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        print("Setting up MJD-ECNPF and MJD-FINEC majors...")
        result = data_importer.setup_specific_majors()
        if result['success']:
            print(f"✓ {result['message']}")
        else:
            print(f"✗ Failed to setup majors")
            return
        
        # Import unit data from CSV if available
        csv_path = "Reference_Material/Data_from_Client/Units with unit rules and availabilities.csv"
        if os.path.exists(csv_path):
            print("Importing unit data from CSV...")
            try:
                import_result = data_importer.import_comprehensive_units_csv(csv_path)
                print(f"✓ Imported {import_result['units_created']} units")
                print(f"✓ Created {import_result['availabilities_created']} availabilities")
            except Exception as e:
                print(f"✗ Failed to import unit data: {e}")
        
        # Show final status
        print("\nDatabase status:")
        status = data_importer.get_import_status()
        for key, value in status.items():
            print(f"  {key}: {value}")

if __name__ == '__main__':
    init_database()