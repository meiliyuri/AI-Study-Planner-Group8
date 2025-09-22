#!/usr/bin/env python3
"""
Prerequisite validation checker for study plans
"""

from app import app, db
from app.models import Unit
import re

def parse_plan_from_text(plan_text):
    """Parse a study plan from copy-pasted text"""
    plan = {}
    current_semester = None

    lines = plan_text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Look for semester headers like "Year 1" or "Semester 1"
        if 'Year' in line and 'Semester' in line:
            current_semester = line
            plan[current_semester] = []
        elif current_semester and len(line) >= 4 and line.isupper() and any(char.isdigit() for char in line):
            # This looks like a unit code (e.g., ECON1101)
            unit_code = line.split()[0]  # Take first word in case there's extra text
            if len(unit_code) >= 4 and unit_code[0:4].isalpha():
                plan[current_semester].append(unit_code)

    return plan

def check_prerequisite(unit_code, prerequisite_text, units_taken_before):
    """Check if prerequisite is satisfied by units taken before this semester"""
    if not prerequisite_text or prerequisite_text.lower() in ['nil', 'none', '']:
        return True, "No prerequisites"

    prereq = prerequisite_text.lower()
    issues = []

    # Look for specific unit codes in prerequisites
    unit_codes_in_prereq = re.findall(r'[A-Z]{4}[0-9]{4}', prerequisite_text.upper())

    for required_unit in unit_codes_in_prereq:
        if required_unit not in units_taken_before:
            issues.append(f"Missing prerequisite: {required_unit}")

    # Check for point requirements
    if 'points' in prereq or 'credit' in prereq:
        # Simplified: assume each unit is 6 points
        total_points = len(units_taken_before) * 6

        # Extract point requirement numbers
        point_matches = re.findall(r'(\d+)\s*points?', prereq)
        if point_matches:
            required_points = int(point_matches[0])
            if total_points < required_points:
                issues.append(f"Insufficient points: {total_points}/{required_points}")

    # Check for level requirements
    if 'level 1' in prereq:
        level_1_count = len([u for u in units_taken_before if len(u) >= 5 and u[4] == '1'])
        if 'level 1 24 points' in prereq and level_1_count * 6 < 24:
            issues.append(f"Insufficient Level 1 points: {level_1_count * 6}/24")

    return len(issues) == 0, "; ".join(issues) if issues else "Prerequisites satisfied"

def validate_plan_prerequisites(plan):
    """Validate all prerequisites in a study plan"""
    print("🔍 PREREQUISITE VALIDATION REPORT")
    print("=" * 50)

    # Track units taken by semester (chronologically)
    units_taken = []
    semester_order = [
        'Year 1, Semester 1', 'Year 1, Semester 2',
        'Year 2, Semester 1', 'Year 2, Semester 2',
        'Year 3, Semester 1', 'Year 3, Semester 2'
    ]

    total_violations = 0

    for semester in semester_order:
        if semester not in plan:
            continue

        print(f"\n📅 {semester}")
        print("-" * 30)

        semester_violations = 0

        for unit_code in plan[semester]:
            # Get unit info from database
            unit = Unit.query.filter_by(code=unit_code).first()

            if not unit:
                print(f"❌ {unit_code}: Unit not found in database")
                semester_violations += 1
                continue

            # Check prerequisites
            is_valid, message = check_prerequisite(unit_code, unit.prerequisites, units_taken)

            if is_valid:
                print(f"✅ {unit_code}: {message}")
            else:
                print(f"❌ {unit_code}: {message}")
                semester_violations += 1

        # Add this semester's units to taken list
        units_taken.extend(plan[semester])

        if semester_violations == 0:
            print(f"✅ All units in {semester} have prerequisites satisfied")
        else:
            print(f"❌ {semester_violations} prerequisite violations in {semester}")
            total_violations += semester_violations

    print(f"\n📊 SUMMARY")
    print("=" * 20)
    if total_violations == 0:
        print("🎉 ALL PREREQUISITES SATISFIED!")
    else:
        print(f"⚠️  {total_violations} total prerequisite violations found")

    return total_violations == 0

if __name__ == "__main__":
    print("Prerequisite Checker Ready!")
    print("Usage: paste your study plan and I'll check all prerequisites")