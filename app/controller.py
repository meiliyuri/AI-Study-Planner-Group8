# Controller functions for AI Study Planner routes, keeping routes.py clean
# Handles all business logic for study plan generation, validation, and export
# Written with the aid of Claude AI for enhanced academic planning capabilities

from app import app, db  # Flask app and SQLAlchemy database instance
from flask import request, jsonify, session, make_response  # Flask request handling functions
from app.models import Unit, Major, MajorUnit, StudyPlan  # Database models for academic data
import json  # JSON parsing and serialization
import io  # Input/output operations for PDF generation
from datetime import datetime  # Date and time utilities
from reportlab.pdfgen import canvas  # PDF generation library
from reportlab.lib.pagesizes import letter, A4  # PDF page size constants
from reportlab.lib import colors  # PDF color utilities
from reportlab.lib.styles import getSampleStyleSheet  # PDF styling utilities
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer  # PDF layout components
from config import Config  # Application configuration
from sqlalchemy import or_ # SQLAlchemy logical operators
import re # Regular expressions for text processing

# Claude AI client setup for enhanced academic reasoning capabilities
from anthropic import Anthropic
claude_client = Anthropic(api_key=Config.CLAUDE_API_KEY)

def extract_json_from_response(text):
    """Extract JSON object from a text response that might contain extra content

    This function handles AI responses that may include explanatory text
    alongside the requested JSON data structure.

    Args:
        text (str): The raw text response from AI that may contain JSON

    Returns:
        str: Extracted JSON string, or None if no valid JSON found
    """
    import re  # Regular expression library for pattern matching

    # Look for JSON object starting with { and ending with }
    json_object_match = re.search(r'\{.*\}', text, re.DOTALL)
    if json_object_match:
        return json_object_match.group(0)

    # Look for JSON array starting with [ and ending with ]
    json_array_match = re.search(r'\[.*\]', text, re.DOTALL)
    if json_array_match:
        return json_array_match.group(0)

    return None  # Return None if no valid JSON structure found

def get_available_majors():
    """Get list of available majors for degree selection

    Retrieves all available academic majors from the database and formats
    them for frontend consumption. Used to populate major selection dropdown.

    Returns:
        JSON response: List of majors with id, code, name, and degree fields
    """
    try:
        # SQLAlchemy query to get all majors from database
        available_majors = Major.query.all()
        majors_list = []  # Initialize empty list for major data

        # Build list of major dictionaries for JSON response
        for individual_major in available_majors:
            major_data = {
                'id': individual_major.id,
                'code': individual_major.code,
                'name': individual_major.name,
                'degree': individual_major.degree
            }
            majors_list.append(major_data)

        # Return JSON response with majors list
        return jsonify({'majors': majors_list})
    except Exception as database_error:
        # Return error response if database operation fails
        return jsonify({'error': str(database_error)}), 500

def generate_initial_plan():
    """Generate an initial study plan using Claude AI

    Creates a comprehensive 3-year study plan based on the selected major,
    considering UWA degree requirements, prerequisites, and semester availability.
    Uses Claude AI for intelligent unit selection and scheduling.

    Returns:
        JSON response: Complete study plan with unit details and electives
    """
    try:
        # Get request data from frontend
        request_data = request.get_json()
        selected_major_id = request_data.get('major_id')
        current_session_id = session.get('session_id')  # Flask session function

        # Validate required parameters
        if not selected_major_id or not current_session_id:
            return jsonify({'error': 'Major ID and session required'}), 400

        # SQLAlchemy query to find the selected major
        selected_major = Major.query.get(selected_major_id)
        if not selected_major:
            return jsonify({'error': 'Major not found'}), 404

        # Get major requirements from database
        major_unit_relationships = MajorUnit.query.filter_by(major_id=selected_major_id).all()  # SQLAlchemy query

        # Separate mandatory and optional units by academic level
        mandatory_units = {'level_1': [], 'level_2': [], 'level_3': []}
        optional_units = {'level_1': [], 'level_2': [], 'level_3': []}

        # Process each unit relationship for the selected major
        for major_unit_relationship in major_unit_relationships:
            # Skip bridging units completely as they are not part of regular degree progression
            if major_unit_relationship.unit.is_bridging:
                continue

            # Categorize units based on requirement type
            if major_unit_relationship.requirement_type == 'core':
                mandatory_units[f'level_{major_unit_relationship.level}'].append(major_unit_relationship.unit.code)
            elif major_unit_relationship.requirement_type == 'option':
                optional_units[f'level_{major_unit_relationship.level}'].append(major_unit_relationship.unit.code)


        # Get additional units from the broader course pool to fill 24 total units
        additional_units = {'level_1': [], 'level_2': [], 'level_3': []}

        # Get non-bridging units that aren't already in the major
        existing_unit_codes = set()
        for level_units in mandatory_units.values():
            existing_unit_codes.update(level_units)
        for level_units in optional_units.values():
            existing_unit_codes.update(level_units)

        # Get suitable additional units for each level
        for level in [1, 2, 3]:
            additional_level_units = Unit.query.filter(
                Unit.level == level,
                Unit.is_bridging == False,
                ~Unit.code.in_(existing_unit_codes)
            ).limit(20).all()  # Get 20 options per level for AI to choose from

            additional_units[f'level_{level}'] = [u.code for u in additional_level_units]


        # Fallback if no units found for major - use typical Economics units
        if not major_unit_relationships:
            mandatory_units = {
                'level_1': ['ECON1101', 'ECON1102', 'STAT1520', 'FINA1221'],
                'level_2': ['ECON2233', 'ECON2234', 'ECON2235', 'ECON2236'],
                'level_3': ['ECON3301', 'ECON3302', 'ECON3303']
            }
            optional_units = {
                'level_1': [],
                'level_2': ['ECON2237', 'ECON2238', 'ECON2239', 'ECON2240', 'ECON2241'],
                'level_3': ['ECON3304', 'ECON3305', 'ECON3306', 'ECON3307', 'ECON3308', 'ECON3309', 'ECON3310', 'ECON3311', 'ECON3312', 'ECON3313']
            }

        # Create Claude prompt with constraint data
        prompt = create_plan_generation_prompt(selected_major, mandatory_units, optional_units, additional_units)

        # Call Claude 3.5 Sonnet with maximum reasoning
        plan_json = call_claude_for_plan_generation(prompt)

        if not plan_json:
            return jsonify({'error': 'Failed to generate plan with Claude'}), 500


        # Parse and validate the response
        try:
            plan_data = json.loads(plan_json)
        except json.JSONDecodeError as e:
            # Try to extract JSON from the response
            cleaned_json = extract_json_from_response(plan_json)
            if cleaned_json:
                try:
                    plan_data = json.loads(cleaned_json)
                except json.JSONDecodeError:
                    return jsonify({'error': f'Invalid plan format from AI: {str(e)}'}), 500
            else:
                return jsonify({'error': f'Invalid plan format from AI: {str(e)}'}), 500

        # Convert new format to old format if needed (for backward compatibility)
        original_plan_data = plan_data.copy()
        for semester, items in plan_data.items():
            if items and isinstance(items[0], dict) and 'unit' in items[0]:
                # New format: convert objects to unit codes
                plan_data[semester] = [item['unit'] for item in items]

        # Save the plan
        study_plan = StudyPlan(
            session_id=current_session_id,
            major_id=selected_major_id,
            plan_data=json.dumps(plan_data),
            is_valid=True
        )
        db.session.add(study_plan)
        db.session.commit()

        # Enrich plan with unit details for frontend
        enriched_plan = {}
        units_in_plan = set()

        for semester, unit_codes in plan_data.items():
            enriched_plan[semester] = []
            for unit_code in unit_codes:
                units_in_plan.add(unit_code)
                unit = Unit.query.filter_by(code=unit_code).first()
                if unit:
                    enriched_plan[semester].append({
                        'code': unit.code,
                        'title': unit.title,
                        'level': unit.level,
                        'points': unit.points,
                        'prerequisites': unit.prerequisites or '',
                        'availabilities': unit.availabilities or '',
                        'corequisites': unit.corequisites or '',
                        'incompatibilities': unit.incompatibilities or ''
                    })
                else:
                    # Fallback for units not in database
                    enriched_plan[semester].append({
                        'code': unit_code,
                        'title': f'Unit {unit_code}',
                        'level': int(unit_code[4]) if len(unit_code) >= 5 and unit_code[4].isdigit() else 1,
                        'points': 6
                    })

        # Calculate unused major electives
        unused_major_electives = []
        for mu in major_unit_relationships:
            if not mu.unit.is_bridging and mu.unit.code not in units_in_plan:
                unused_major_electives.append({
                    'code': mu.unit.code,
                    'title': mu.unit.title,
                    'level': mu.unit.level,
                    'points': mu.unit.points,
                    'prerequisites': mu.unit.prerequisites or '',
                    'availabilities': mu.unit.availabilities or '',
                    'corequisites': mu.unit.corequisites or '',
                    'incompatibilities': mu.unit.incompatibilities or '',
                    'requirement_type': mu.requirement_type
                })

        # Get degree-specific general electives
         # === General Electives (prefix 보강 없이, 학위코드 매칭만) ===
        course_code = (getattr(selected_major, 'degree_code', '') or '').strip().upper()

        # units_in_plan은 위에서 enriched_plan 만들 때 이미 채웠으니 그대로 사용
        general_electives = find_general_electives_by_degree(course_code, units_in_plan, limit=200)

        # 중복 제거 + 정렬 + 제한
        seen_codes = set()
        unique_general_electives = []
        for unit in general_electives:
            if unit['code'] not in seen_codes:
                seen_codes.add(unit['code'])
                unique_general_electives.append(unit)

        unique_general_electives.sort(key=lambda x: (x['level'], x['code']))

        return jsonify({
            'plan': plan_data,                 # Keep original for compatibility
            'enriched_plan': enriched_plan,    # Add enriched version
            'major_electives': unused_major_electives,
            'general_electives': unique_general_electives[:200],  # Limit to 200 일단은 제한 둠
            'major': {
                'code': selected_major.code,
                'name': selected_major.name,
                'degree': selected_major.degree,
                'degree_code': course_code,    # 디버깅/프론트 표시용
            }
        })


    except Exception as e:
        return jsonify({'error': str(e)}), 500

def validate_study_plan():
    """Validate a modified study plan using OpenAI"""
    try:
        data = request.get_json()
        plan_data = data.get('plan')
        session_id = session.get('session_id')

        if not plan_data or not session_id:
            return jsonify({'error': 'Plan data and session required'}), 400

        # Get the current study plan
        study_plan = StudyPlan.query.filter_by(session_id=session_id).first()
        if not study_plan:
            return jsonify({'error': 'No study plan found for session'}), 404

        major = study_plan.major

        # Validate the plan programmatically (don't use AI for counting!)
        validation_result = validate_plan_programmatically(plan_data)

        # Update the study plan
        study_plan.plan_data = json.dumps(plan_data)
        study_plan.is_valid = validation_result.get('isValid', False)
        study_plan.validation_errors = validation_result.get('reason', '')
        db.session.commit()

        return jsonify(validation_result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def get_available_units():
    """Get list of available units for drag and drop"""
    try:
        # Levels 1–3 only, excluding bridging
        units = Unit.query.filter(
            Unit.is_bridging == False,
            Unit.level.in_([1, 2, 3])
        ).all()

        units_list = []
        for unit in units:
            units_list.append({
                'code': unit.code,
                'title': unit.title,
                'level': unit.level,
                'points': unit.points,
                'availabilities': unit.availabilities,
                'prerequisites': unit.prerequisites,
                'corequisites': unit.corequisites,
                'incompatibilities': unit.incompatibilities
            })

        return jsonify({'units': units_list})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def export_plan_to_pdf():
    """Export the current study plan to PDF"""
    try:
        # Get plan data from request
        data = request.get_json()
        if not data or 'plan' not in data:
            return jsonify({'error': 'Plan data required'}), 400

        plan = data['plan']

        # Create PDF in memory
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = styles['Title']
        heading_style = styles['Heading2']
        normal_style = styles['Normal']

        # Title
        title = Paragraph("Study Plan", title_style)
        elements.append(title)
        elements.append(Spacer(1, 20))

        # Generated timestamp
        timestamp = Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", normal_style)
        elements.append(timestamp)
        elements.append(Spacer(1, 20))

        # Process each semester
        semester_order = [
            'Year 1, Semester 1', 'Year 1, Semester 2',
            'Year 2, Semester 1', 'Year 2, Semester 2',
            'Year 3, Semester 1', 'Year 3, Semester 2'
        ]

        for semester in semester_order:
            if semester in plan and plan[semester]:
                # Semester heading
                heading = Paragraph(semester, heading_style)
                elements.append(heading)
                elements.append(Spacer(1, 10))

                # Get unit details from database
                unit_codes = plan[semester]
                table_data = [['Unit Code', 'Title', 'Level', 'Points']]

                for unit_code in unit_codes:
                    unit = Unit.query.filter_by(code=unit_code).first()
                    if unit:
                        table_data.append([
                            unit.code,
                            unit.title or 'Unknown Title',
                            str(unit.level or ''),
                            str(unit.points or '')
                        ])
                    else:
                        # Unit not found in database
                        table_data.append([unit_code, 'Unit not found', '', ''])

                # Create table
                table = Table(table_data, colWidths=[80, 300, 50, 50])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))

                elements.append(table)
                elements.append(Spacer(1, 20))

        # Build PDF
        doc.build(elements)
        pdf_data = buffer.getvalue()
        buffer.close()

        # Create response
        response = make_response(pdf_data)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename="study_plan_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'

        return response

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def ai_validate_plan():
    """AI-powered comprehensive study plan quality validation"""
    try:
        # Get plan data from request
        data = request.get_json()
        if not data or 'plan' not in data or 'major_code' not in data:
            return jsonify({'error': 'Plan data and major_code required'}), 400

        plan = data['plan']
        major_id = data['major_code']  # Frontend sends ID, not code

        # Validate input
        if not plan or not major_id:
            return jsonify({'error': 'Invalid plan or major_id'}), 400

        # Get major information by ID
        major = Major.query.get(major_id)
        if not major:
            return jsonify({'error': 'Major not found'}), 404

        # Prepare plan summary for AI analysis
        total_units = sum(len(units) for units in plan.values())
        if total_units == 0:
            return jsonify({'error': 'Empty study plan'}), 400

        # Count units by level
        level_counts = {1: 0, 2: 0, 3: 0}
        all_unit_codes = []

        for semester_units in plan.values():
            for unit_code in semester_units:
                all_unit_codes.append(unit_code)
                # Extract level from unit code (5th character)
                if len(unit_code) >= 5 and unit_code[4].isdigit():
                    level = int(unit_code[4])
                    level_counts[level] = level_counts.get(level, 0) + 1

        # Get detailed unit information from database
        unit_details = {}
        for unit_code in all_unit_codes:
            unit = Unit.query.filter_by(code=unit_code).first()
            if unit:
                unit_details[unit_code] = {
                    'title': unit.title,
                    'level': unit.level,
                    'points': unit.points,
                    'prerequisites': unit.prerequisites,
                    'availabilities': unit.availabilities
                }

        # Call Claude AI for comprehensive analysis
        quality_result = _analyze_plan_with_claude(plan, major, unit_details, level_counts, total_units)

        # Add metadata
        quality_result['metadata'] = {
            'majorInfo': {
                'title': major.name,
                'code': major.code
            },
            'planSummary': {
                'totalUnits': total_units,
                'levelDistribution': level_counts
            }
        }

        return jsonify(quality_result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _analyze_plan_with_claude(plan, major, unit_details, level_counts, total_units):
    """Perform comprehensive AI analysis using Claude"""
    try:
        # Prepare detailed plan information for Claude
        plan_summary = f"Major: {major.name} ({major.code})\n"
        plan_summary += f"Total Units: {total_units}/24\n"
        plan_summary += f"Level Distribution: L1: {level_counts[1]}/12, L2: {level_counts[2]}, L3: {level_counts[3]}/6\n\n"

        # Add semester by semester breakdown
        plan_summary += "Study Plan:\n"
        for semester, units in plan.items():
            plan_summary += f"\n{semester}:\n"
            for unit_code in units:
                unit_info = unit_details.get(unit_code, {})
                title = unit_info.get('title', 'Unknown')
                prereqs = unit_info.get('prerequisites', 'Unknown')
                plan_summary += f"  • {unit_code}: {title}\n"
                if prereqs and prereqs != 'Nil':
                    plan_summary += f"    Prerequisites: {prereqs}\n"

        # Create comprehensive prompt for Claude
        prompt = f"""You are a UWA academic advisor analyzing a Bachelor's degree study plan. Provide a comprehensive quality assessment focusing on academic excellence and university requirements.

# Plan to Analyze
{plan_summary}

# Analysis Framework
Evaluate this study plan across these key dimensions:

1. **Complex Constraint Analysis**: Points distribution, prerequisite chains, temporal logic
2. **Domain Coherence**: Unit selection alignment with major goals and career pathways
3. **Academic Progression**: Logical skill building, knowledge scaffolding across years
4. **University Policy Compliance**: UWA degree requirements, level distributions
5. **Career Pathway Optimization**: Industry relevance, specialization focus

# Specific UWA Requirements to Validate
- Total 24 units (currently {total_units})
- Maximum 12 Level 1 units (currently {level_counts[1]})
- Minimum 6 Level 3 units (currently {level_counts[3]})
- Prerequisites must be completed before dependent units
- Semester availability constraints

# Quality Assessment Guidelines
- Quality Score: 0-100% based on overall academic soundness
- Focus on actionable improvements, not just compliance
- Consider both technical requirements AND educational value
- Identify opportunities for enhanced learning outcomes

Provide your assessment in the following JSON format:
{{
    "overallQuality": "excellent|good|fair|poor",
    "qualityScore": 85,
    "recommendations": ["specific actionable suggestions"],
    "warnings": ["critical issues requiring attention"],
    "strengths": ["positive aspects of the plan"],
    "academicProgression": "detailed analysis of learning progression",
    "levelDistribution": "assessment of unit level balance",
    "majorCoherence": "evaluation of major-specific unit selection",
    "constraintCompliance": "assessment of UWA policy adherence",
    "careerPathway": "analysis of career preparation value"
}}"""

        # Make API call to Claude
        import anthropic

        claude_client = anthropic.Anthropic(api_key=Config.CLAUDE_API_KEY)

        response = claude_client.messages.create(
            model="claude-opus-4-1-20250805",  # Using Claude Opus 4.1 - same as plan generation
            max_tokens=2000,
            temperature=0.3,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        # Parse Claude's response
        response_text = response.content[0].text.strip()

        # Extract JSON from response
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            json_text = response_text[json_start:json_end].strip()
        else:
            # Try to find JSON object in response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start != -1 and json_end > json_start:
                json_text = response_text[json_start:json_end]
            else:
                raise Exception("Could not extract JSON from Claude response")

        result = json.loads(json_text)

        # Ensure all required fields are present
        result.setdefault('overallQuality', 'fair')
        result.setdefault('qualityScore', 70)
        result.setdefault('recommendations', [])
        result.setdefault('warnings', [])
        result.setdefault('strengths', [])
        result.setdefault('academicProgression', 'Analysis unavailable')
        result.setdefault('levelDistribution', 'Analysis unavailable')
        result.setdefault('majorCoherence', 'Analysis unavailable')
        result.setdefault('constraintCompliance', 'Analysis unavailable')
        result.setdefault('careerPathway', 'Analysis unavailable')

        return result

    except Exception as e:
        # Return fallback response if AI analysis fails
        return {
            "overallQuality": "unknown",
            "qualityScore": 50,
            "recommendations": ["AI analysis temporarily unavailable - please validate manually"],
            "warnings": [f"AI validation error: {str(e)}"],
            "strengths": ["Plan structure appears complete"],
            "academicProgression": "Unable to assess - AI service unavailable",
            "levelDistribution": f"L1: {level_counts[1]}/12, L2: {level_counts[2]}, L3: {level_counts[3]}/6",
            "majorCoherence": "Unable to assess - AI service unavailable",
            "constraintCompliance": "Basic requirements appear met",
            "careerPathway": "Unable to assess - AI service unavailable"
        }

def _field_has_degree(field_value: str, degree_code: str) -> bool:
    """homedegree / degreestaughtin 문자열에서 ; 또는 , 로 구분된 토큰에 degree_code가 포함되는지 정확 매칭"""
    if not field_value or not degree_code:
        return False
    tokens = [t.strip().upper() for t in re.split(r'[;,]', field_value) if t.strip()]
    return degree_code.upper() in tokens

def find_general_electives_by_degree(degree_code: str, units_in_plan: set, limit: int = 200):
    if not degree_code:
        return []
    dc = degree_code.upper()

    # 1차: 포함 검색으로 후보 수집
    rows = Unit.query.filter(
        Unit.is_bridging == False,
        ~Unit.code.in_(units_in_plan),
        or_(
            Unit.homedegree.ilike(f'%{degree_code}%'),
            Unit.degreestaughtin.ilike(f'%{degree_code}%')
        )
    ).limit(limit).all()

    # Secondary: Token-level exact matching
    out, seen = [], set()
    for u in rows:
        ok = _field_has_degree(u.homedegree or '', dc) or _field_has_degree(u.degreestaughtin or '', dc)
        if not ok or u.code in seen:
            continue
        seen.add(u.code)
        out.append({
            'code': u.code,
            'title': u.title,
            'level': u.level,
            'points': u.points,
            'prerequisites': u.prerequisites or '',
            'availabilities': u.availabilities or '',
            'corequisites': u.corequisites or '',
            'incompatibilities': u.incompatibilities or ''
        })
    return out


def import_course_data():
    """Import course data from uploaded files"""
    # TODO: Implement data import functionality
    return jsonify({'message': 'Data import not yet implemented'}), 501

def clear_plan_cache():
    """Clear cached study plans"""
    try:
        StudyPlan.query.delete()
        db.session.commit()
        return jsonify({'message': 'Plan cache cleared successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def call_claude_for_plan_generation(prompt):
    """Call Claude Opus 4.1 with maximum reasoning capabilities for plan generation"""
    try:
        # Claude Opus 4.1 - Latest and most powerful model with maximum reasoning settings
        response = claude_client.messages.create(
            model="claude-opus-4-1-20250805",  # Claude Opus 4.1 - Latest model
            max_tokens=4096,  # Maximum reasoning capability
            temperature=0.1,  # Low temperature for consistency in constraint satisfaction
            messages=[
                {
                    "role": "user",
                    "content": f"""Think step by step and use maximum reasoning to solve this complex constraint satisfaction problem. Apply ultra-careful analysis to ensure all temporal dependencies and constraints are satisfied.

{prompt}

Use deep reasoning to verify:
1. All prerequisites are in earlier semesters than dependent units
2. All units are placed in semesters where they're available
3. No temporal logic violations occur
4. All degree requirements are met

Reason through each placement decision carefully."""
                }
            ]
        )

        plan_content = response.content[0].text if response.content else None

        if not plan_content:
            return None

        return plan_content

    except Exception as e:
        return None

def create_plan_generation_prompt(major, mandatory_units, optional_units, additional_units):
    """Create OpenAI prompt for intelligent plan generation with STRATEGY 2: Pre-split by availability"""

    # Count total mandatory and optional units from major
    total_major_units = sum(len(units) for units in mandatory_units.values()) + sum(len(units) for units in optional_units.values())
    units_needed = 24 - total_major_units

    # Gather all unit codes and split by availability
    all_unit_codes = []
    for level_units in mandatory_units.values():
        all_unit_codes.extend(level_units)
    for level_units in optional_units.values():
        all_unit_codes.extend(level_units)
    for level_units in additional_units.values():
        all_unit_codes.extend(level_units[:10])  # Limit additional units

    # STRATEGY 2: Pre-split units by semester availability
    semester_1_units = {'level_1': [], 'level_2': [], 'level_3': []}
    semester_2_units = {'level_1': [], 'level_2': [], 'level_3': []}
    both_semesters_units = {'level_1': [], 'level_2': [], 'level_3': []}

    # Build constraint information AND split by availability
    constraint_info = []
    for unit_code in all_unit_codes:
        unit = Unit.query.filter_by(code=unit_code).first()
        if not unit:
            continue

        # Determine level
        if len(unit_code) >= 5 and unit_code[4].isdigit():
            level = int(unit_code[4])
            level_key = f'level_{level}' if level in [1, 2, 3] else None
        else:
            level_key = None

        # Determine availability and add to appropriate list
        availability_text = ""
        if unit.availabilities and unit.availabilities.strip():
            if 'Semester 1' in unit.availabilities and 'Semester 2' not in unit.availabilities:
                availability_text = " - SEMESTER 1 ONLY"
                if level_key: semester_1_units[level_key].append(unit_code)
            elif 'Semester 2' in unit.availabilities and 'Semester 1' not in unit.availabilities:
                availability_text = " - SEMESTER 2 ONLY"
                if level_key: semester_2_units[level_key].append(unit_code)
            else:
                availability_text = " - Available both semesters"
                if level_key: both_semesters_units[level_key].append(unit_code)
        else:
            # No availability info = assume available both semesters
            availability_text = " - Available both semesters"
            if level_key: both_semesters_units[level_key].append(unit_code)

        # Build constraint info for display
        if unit.prerequisites or unit.availabilities:
            info = f"• {unit_code}"

            # Extract and clean prerequisite unit codes
            if unit.prerequisites and unit.prerequisites.strip() and unit.prerequisites.lower() != 'nil':
                import re
                prereq_units = re.findall(r'[A-Z]{4}[0-9]{4}', unit.prerequisites)
                if prereq_units:
                    info += f" - Needs: {' OR '.join(prereq_units)}"
                else:
                    # Handle point requirements or other text
                    if 'points' in unit.prerequisites.lower():
                        info += f" - Needs: 48+ points"
                    else:
                        info += f" - Prerequisites: {unit.prerequisites[:50]}..."

            info += availability_text

            if len(info) > len(f"• {unit_code}"):  # Only add if there's constraint info
                constraint_info.append(info)

    constraints_text = "\n".join(constraint_info[:20]) if constraint_info else "No specific constraints for listed units."

    prompt = f"""You are an expert academic advisor creating a 3-year study plan for the {major.name} major ({major.code}).

# CRITICAL REQUIREMENTS:
- EXACTLY 24 units total (4 per semester × 6 semesters)
- Maximum 12 Level 1 units (≤12 units with codes ending in 1xxx)
- Minimum 12 Level 2/3 units (≥12 units with codes ending in 2xxx or 3xxx)
- Minimum 6 Level 3 units (≥6 units with codes ending in 3xxx)

# LEVEL PROGRESSION STRATEGY:
- Year 1: Primarily Level 1 units (some Level 2 if needed)
- Year 2: Mix of Level 1 and Level 2 units
- Year 3: Level 2 and Level 3 units (NO Level 1 unless essential)

# STRATEGY 2: SEMESTER-SPECIFIC UNIT POOLS
Use ONLY these semester-specific pools. DO NOT place units in semesters where they're not available:

## SEMESTER 1 ONLY UNITS (can ONLY be placed in odd semesters):
Level 1: {semester_1_units['level_1']}
Level 2: {semester_1_units['level_2']}
Level 3: {semester_1_units['level_3']}

## SEMESTER 2 ONLY UNITS (can ONLY be placed in even semesters):
Level 1: {semester_2_units['level_1']}
Level 2: {semester_2_units['level_2']}
Level 3: {semester_2_units['level_3']}

## FLEXIBLE UNITS (available both semesters):
Level 1: {both_semesters_units['level_1']}
Level 2: {both_semesters_units['level_2']}
Level 3: {both_semesters_units['level_3']}

# PRIORITY REQUIREMENTS:
1. **MANDATORY CORE units** (must be included from appropriate pools):
   Level 1: {mandatory_units['level_1']}
   Level 2: {mandatory_units['level_2']}
   Level 3: {mandatory_units['level_3']}

2. **MAJOR OPTIONAL units** (fill remaining major slots from appropriate pools):
   Level 1: {optional_units['level_1']}
   Level 2: {optional_units['level_2']}
   Level 3: {optional_units['level_3']}

# CONSTRAINT INFO:
{constraints_text}

# 🚨 CRITICAL TEMPORAL LOGIC RULES (NEVER VIOLATE):
## PREREQUISITES CREATE TIME-BASED DEPENDENCIES:
- If Unit B requires Unit A, then Unit A must be in an EARLIER semester than Unit B
- NEVER place a unit and its prerequisite in the same semester
- NEVER place a unit before its prerequisite has been completed
- Before placing any unit, CHECK that ALL its prerequisites appear in prior semesters

## EXAMPLES OF TEMPORAL VIOLATIONS TO AVOID:
❌ WRONG: ECON2234 (needs ECON1102) in same semester as ECON1102
❌ WRONG: PHAR2220 (needs PHAR2210) but PHAR2210 never included
❌ WRONG: Any Level 2/3 unit without its Level 1 prerequisites completed first

✅ CORRECT: ECON1102 in Year 1 → ECON2234 in Year 2 or later
✅ CORRECT: All prerequisites in earlier semesters before dependent units

# PLACEMENT RULES (STRICTLY ENFORCED):
1. **TEMPORAL SEQUENCING**: Prerequisites must be in EARLIER semesters (never same semester)
2. **ODD SEMESTERS** (1, 3, 5): Use Semester 1 Only + Flexible units
3. **EVEN SEMESTERS** (2, 4, 6): Use Semester 2 Only + Flexible units
4. **DOMAIN COHERENCE**: Don't mix unrelated domains (avoid random PHAR/NEUR units without proper chains)
5. **LEVEL PROGRESSION**: Level 1 → Level 2 → Level 3

# INTELLIGENT SELECTION:
- Include ALL mandatory core units first
- Add major optional units strategically
- Fill remaining {units_needed} slots with appropriate level units
- Balance semester loads (4 units each)
- Respect semester availability restrictions ABSOLUTELY

RESPOND WITH ONLY JSON (no explanation):
{{
  "Year 1, Semester 1": ["UNIT1", "UNIT2", "UNIT3", "UNIT4"],
  "Year 1, Semester 2": ["UNIT1", "UNIT2", "UNIT3", "UNIT4"],
  "Year 2, Semester 1": ["UNIT1", "UNIT2", "UNIT3", "UNIT4"],
  "Year 2, Semester 2": ["UNIT1", "UNIT2", "UNIT3", "UNIT4"],
  "Year 3, Semester 1": ["UNIT1", "UNIT2", "UNIT3", "UNIT4"],
  "Year 3, Semester 2": ["UNIT1", "UNIT2", "UNIT3", "UNIT4"]
}}"""

    return prompt

def validate_plan_programmatically(plan_data):
    """Validate study plan using proper programming logic (not AI counting!)"""

    # Collect all units from the plan
    all_units = []
    for semester, units in plan_data.items():
        all_units.extend(units)

    # Count units by level (extract level from unit code 5th character)
    level_1_units = []
    level_2_units = []
    level_3_units = []

    for unit_code in all_units:
        if len(unit_code) >= 5 and unit_code[4].isdigit():
            level = int(unit_code[4])
            if level == 1:
                level_1_units.append(unit_code)
            elif level == 2:
                level_2_units.append(unit_code)
            elif level == 3:
                level_3_units.append(unit_code)

    total_units = len(all_units)
    level_1_count = len(level_1_units)
    level_2_count = len(level_2_units)
    level_3_count = len(level_3_units)
    level_2_3_count = level_2_count + level_3_count

    # Validation rules - separate critical errors from warnings
    critical_errors = []
    warnings = []

    # Rule 1: Total units - warn if incomplete, error if too many
    if total_units > 24:
        critical_errors.append(f"Plan has {total_units} units, but maximum allowed is 24.")
    elif total_units < 24:
        warnings.append(f"Plan has {total_units} units, target is 24 units ({24 - total_units} more needed).")

    # Rule 2: Semester capacity - warn if incomplete, error if too many
    for semester, units in plan_data.items():
        if len(units) > 4:
            critical_errors.append(f"{semester} has {len(units)} units, but maximum allowed is 4.")
        elif 0 < len(units) < 4:
            warnings.append(f"{semester} has {len(units)} units, target is 4 units.")

    # Rule 3: Maximum 12 Level 1 units - always critical error if exceeded
    if level_1_count > 12:
        critical_errors.append(f"There are {level_1_count} Level 1 units which exceeds the maximum of 12.")

    # Rule 4: Minimum 12 Level 2 or Level 3 units
    if level_2_3_count < 8:  # Really low
        critical_errors.append(f"There are only {level_2_3_count} Level 2 or Level 3 units, minimum required is 12.")
    elif level_2_3_count < 12:
        warnings.append(f"There are only {level_2_3_count} Level 2 or Level 3 units, minimum required is 12.")

    # Rule 5: Minimum 6 Level 3 units
    if level_3_count < 3:
        critical_errors.append(f"There are only {level_3_count} Level 3 units, minimum required is 6.")
    elif level_3_count < 6:
        warnings.append(f"There are only {level_3_count} Level 3 units, minimum required is 6.")

    # Return validation result
    if critical_errors:
        return {
            'isValid': False,
            'reason': "Critical issues found: " + " ".join(critical_errors),
            'type': 'error',
            'errors': critical_errors,   
            'warnings': warnings,        
        }
    elif warnings:
        return {
            'isValid': True,  # Valid but incomplete
            'reason': "Plan incomplete: " + warnings[0],  
            'type': 'warning',
            'errors': [],                  
            'warnings': warnings,
        }
    else:
        return {
            'isValid': True,
            'reason': 'Plan meets all UWA degree requirements',
            'type': 'success',
            'errors': [],
            'warnings': [],
        }

def create_validation_prompt(major, plan_data):
    """Create OpenAI prompt for plan validation"""
    prompt = f"""Validate the following study plan for {major.name} major ({major.code}) against UWA degree requirements.

# Plan to validate:
{json.dumps(plan_data, indent=2)}

# Validation Rules:
1. Total of 24 units across 6 semesters
2. Exactly 4 units per semester
3. Maximum 12 Level 1 units (codes ending in 1xxx)
4. Minimum 12 Level 2 or Level 3 units (codes ending in 2xxx or 3xxx)
5. Minimum 6 Level 3 units (codes ending in 3xxx)

Check each rule and respond with JSON:
{{
  "isValid": true/false,
  "reason": "Detailed explanation of any violations or 'Plan is valid'"
}}"""

    return prompt