#!/usr/bin/env python3
"""
Fix the major setup to ensure correct unit classifications
"""

from app import create_app, db
from app.models import MajorUnit, Major
from app.data_import import data_importer

def fix_majors():
    """Clear existing major-unit relationships and recreate them correctly"""
    app = create_app()
    
    with app.app_context():
        print("Clearing existing major-unit relationships...")
        
        # Get the majors
        major_ecnpf = Major.query.filter_by(code='MJD-ECNPF').first()
        major_finec = Major.query.filter_by(code='MJD-FINEC').first()
        
        if not major_ecnpf or not major_finec:
            print("Majors not found. Run init_majors.py first.")
            return
        
        # Clear existing relationships
        MajorUnit.query.filter_by(major_id=major_ecnpf.id).delete()
        MajorUnit.query.filter_by(major_id=major_finec.id).delete()
        
        db.session.commit()
        print("Cleared existing relationships.")
        
        # Recreate relationships with correct classifications
        print("Setting up ECNPF requirements...")
        data_importer._setup_ecnpf_requirements(major_ecnpf)
        
        print("Setting up FINEC requirements...")
        data_importer._setup_finec_requirements(major_finec)
        
        db.session.commit()
        
        # Show results
        print("\nFinal status:")
        ecnpf_core = MajorUnit.query.filter_by(major_id=major_ecnpf.id, unit_type='core').count()
        ecnpf_option = MajorUnit.query.filter_by(major_id=major_ecnpf.id, unit_type='option').count()
        
        finec_core = MajorUnit.query.filter_by(major_id=major_finec.id, unit_type='core').count()
        finec_option = MajorUnit.query.filter_by(major_id=major_finec.id, unit_type='option').count()
        
        print(f"ECNPF: {ecnpf_core} core units, {ecnpf_option} option units")
        print(f"FINEC: {finec_core} core units, {finec_option} option units")

if __name__ == '__main__':
    fix_majors()