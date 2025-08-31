#!/usr/bin/env python3
"""
Demo Data Processor for AI Study Planner
Shows how the data can be processed without external dependencies
"""

import csv
import json
import sqlite3
import os
import sys
from datetime import datetime

def create_database():
    """Create SQLite database with necessary tables"""
    conn = sqlite3.connect('study_planner_demo.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            prerequisites_raw TEXT,
            corequisites_raw TEXT,
            availabilities_raw TEXT,
            credit_points INTEGER DEFAULT 6,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS courses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS course_units (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            course_id INTEGER,
            unit_id INTEGER,
            unit_type TEXT,
            sequence_order INTEGER,
            FOREIGN KEY (course_id) REFERENCES courses (id),
            FOREIGN KEY (unit_id) REFERENCES units (id)
        )
    ''')
    
    conn.commit()
    return conn

def import_units_from_csv(conn, file_path):
    """Import units from CSV file"""
    cursor = conn.cursor()
    units_imported = 0
    
    print(f"Importing units from {file_path}...")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                try:
                    cursor.execute('''
                        INSERT OR IGNORE INTO units 
                        (code, title, prerequisites_raw, corequisites_raw, availabilities_raw)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        row.get('code', ''),
                        row.get('title', ''),
                        row.get('RulesPrereqs', ''),
                        row.get('RulesCoreqs', ''),
                        row.get('Availabilities', '')
                    ))
                    if cursor.rowcount > 0:
                        units_imported += 1
                except sqlite3.Error as e:
                    print(f"Error inserting unit {row.get('code', 'unknown')}: {e}")
                    continue
        
        conn.commit()
        print(f"✓ Imported {units_imported} units")
        return units_imported
        
    except FileNotFoundError:
        print(f"✗ File not found: {file_path}")
        return 0
    except Exception as e:
        print(f"✗ Error importing units: {e}")
        return 0

def create_demo_courses(conn):
    """Create demo courses manually since XLSX processing needs pandas"""
    cursor = conn.cursor()
    
    demo_courses = [
        ('MJD-FINEC', 'Financial Economics'),
        ('MJD-ECNPF', 'Economics')
    ]
    
    for code, title in demo_courses:
        cursor.execute('''
            INSERT OR IGNORE INTO courses (code, title)
            VALUES (?, ?)
        ''', (code, title))
    
    conn.commit()
    print(f"✓ Created {len(demo_courses)} demo courses")
    return len(demo_courses)

def analyze_data(conn):
    """Analyze the imported data and show structure"""
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print("DATA ANALYSIS")
    print("="*50)
    
    # Count records
    cursor.execute("SELECT COUNT(*) FROM units")
    unit_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM courses")
    course_count = cursor.fetchone()[0]
    
    print(f"Total Units: {unit_count}")
    print(f"Total Courses: {course_count}")
    
    # Sample units with prerequisites
    print("\nSample Units with Prerequisites:")
    cursor.execute('''
        SELECT code, title, prerequisites_raw 
        FROM units 
        WHERE prerequisites_raw IS NOT NULL 
        AND prerequisites_raw != '' 
        LIMIT 5
    ''')
    
    for code, title, prereqs in cursor.fetchall():
        print(f"  {code}: {title}")
        print(f"    Prerequisites: {prereqs[:100]}...")
    
    # Economics units
    print("\nEconomics Units (ECON*):")
    cursor.execute('''
        SELECT code, title, prerequisites_raw
        FROM units 
        WHERE code LIKE 'ECON%'
        ORDER BY code
        LIMIT 10
    ''')
    
    for code, title, prereqs in cursor.fetchall():
        print(f"  {code}: {title}")
        if prereqs:
            print(f"    Prerequisites: {prereqs}")

def simulate_ai_processing(conn):
    """Simulate AI processing of prerequisite rules"""
    cursor = conn.cursor()
    
    print("\n" + "="*50) 
    print("AI PROCESSING SIMULATION")
    print("="*50)
    
    # Get some sample units for AI processing
    cursor.execute('''
        SELECT code, title, prerequisites_raw
        FROM units 
        WHERE code LIKE 'ECON%' 
        AND prerequisites_raw IS NOT NULL 
        AND prerequisites_raw != ''
        LIMIT 3
    ''')
    
    print("Sample prerequisite rules that AI would process:")
    for code, title, prereqs in cursor.fetchall():
        print(f"\nUnit: {code} - {title}")
        print(f"Raw Prerequisites: {prereqs}")
        
        # Simulate AI interpretation
        if "ECON" in prereqs:
            print("  AI Analysis: Requires previous ECON unit(s)")
        if "completion of" in prereqs.lower():
            print("  AI Analysis: Requires completion of prior study")
        if "or" in prereqs.lower():
            print("  AI Analysis: Has alternative prerequisite options")

def generate_sample_study_plan():
    """Generate a sample study plan structure"""
    print("\n" + "="*50)
    print("SAMPLE STUDY PLAN GENERATION")
    print("="*50)
    
    # This would normally be done by AI, but we'll create a simple example
    sample_plan = {
        "Year 1, Semester 1": ["ECON1101", "MATH1014", "STAT1400", "PHIL1001"],
        "Year 1, Semester 2": ["ECON1102", "MATH1019", "STAT1401", "ENGL1000"],
        "Year 2, Semester 1": ["ECON2233", "ECON2234", "MATH2021", "POLI2000"],
        "Year 2, Semester 2": ["ECON2235", "ECON3301", "FINC2000", "MGMT2000"]
    }
    
    print("Sample AI-Generated Study Plan for Financial Economics:")
    for semester, units in sample_plan.items():
        print(f"\n{semester}:")
        for unit in units:
            print(f"  - {unit}")
    
    return sample_plan

def main():
    """Main demo function"""
    print("AI Study Planner - Data Processing Demo")
    print("=" * 50)
    
    # Create database
    conn = create_database()
    print("✓ Database created/connected")
    
    # Import data
    units_file = "Reference_Material/Data_from_Client/Units.csv"
    import_units_from_csv(conn, units_file)
    
    # Create demo courses
    create_demo_courses(conn)
    
    # Analyze the data
    analyze_data(conn)
    
    # Simulate AI processing
    simulate_ai_processing(conn)
    
    # Generate sample plan
    sample_plan = generate_sample_study_plan()
    
    # Save sample plan to JSON
    with open('sample_study_plan.json', 'w') as f:
        json.dump(sample_plan, f, indent=2)
    print("\n✓ Sample plan saved to sample_study_plan.json")
    
    conn.close()
    print("\n✓ Demo completed successfully!")
    print("\nNext steps:")
    print("1. Install Flask dependencies: pip install flask flask-sqlalchemy openai pandas")
    print("2. Run the full application: python app.py")
    print("3. Import data: python import_data.py")

if __name__ == '__main__':
    main()