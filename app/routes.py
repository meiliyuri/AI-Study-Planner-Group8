# Flask routes for the AI Study Planner web application
# Written with the aid of Claude AI assistant
#
# This file handles all the web requests and responses:
# 
# Main user routes:
# - / (index): Shows available degree programs (homepage)
# - /degree/<code>: Shows study plan for a specific degree program
# 
# API endpoints (AJAX calls from JavaScript):
# - /api/validate_plan: Validates user's modified study plan
# - /api/export_pdf: Generates PDF of study plan
#
# Admin routes:
# - /admin/majors: Interface to enable/disable majors
# - /admin/majors/toggle/<code>: Enable/disable specific major
# - /admin/import_status: Shows database import status
#
# The main flow: User visits homepage -> selects degree -> gets AI-generated plan -> can modify via drag-and-drop

from flask import Blueprint, render_template, request, jsonify, send_file
from app.models import DegreeProgram, BachelorDegree, Major, Unit, MajorUnit
from app.ai_service import ai_service
from app.pdf_generator import generate_study_plan_pdf
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Main page showing available degree programs"""
    degree_programs = DegreeProgram.query.filter_by(is_active=True).order_by(DegreeProgram.display_title).all()
    return render_template('index.html', degree_programs=degree_programs)

@bp.route('/degree/<program_code>')
def degree_view(program_code):
    """
    Main degree page - shows study plan for a specific program like BEC-ECNPF
    This is where users see their AI-generated study plan and can modify it
    """
    # Look up the degree program using the code from the URL (e.g., "BEC-ECNPF")
    degree_program = DegreeProgram.query.filter_by(code=program_code).first()
    if not degree_program:
        return "Degree program not found", 404
    
    # Get all units that belong to this major from the database
    # This SQLAlchemy query joins MajorUnit and Unit tables to get full unit details
    major_units = MajorUnit.query.filter_by(major_id=degree_program.major_id).join(Unit).all()
    
    # Separate units into three lists based on their type
    # Core = required units, Option = choose some, Elective = general electives
    core_units = []
    option_units = []
    elective_units = []
    
    # Loop through each unit in this major and organize them by type
    for major_unit in major_units:
        # Create a simple dictionary with all the unit information we need
        # This makes it easier to pass to the template and AI service
        unit_data = {
            'code': major_unit.unit.code,                    # e.g., "ECON1101"
            'title': major_unit.unit.title,                  # e.g., "Microeconomics: Prices and Markets"
            'prerequisites_raw': major_unit.unit.prerequisites_raw,  # e.g., "MATH1011 or equivalent"
            'corequisites_raw': major_unit.unit.corequisites_raw,    # Units to take at same time
            'credit_points': major_unit.unit.credit_points,  # Usually 6 points per unit
            'unit_type': major_unit.unit_type,               # "core", "option", or "elective"
            'year_level': major_unit.year_level,             # 1, 2, or 3
            'is_mandatory': major_unit.is_mandatory          # True if required, False if optional
        }
        
        # Put this unit into the right list based on its type
        # Core units are required, option units are choose-some-from-these, electives are anything
        if major_unit.unit_type == 'core':
            core_units.append(unit_data)
        elif major_unit.unit_type == 'option':
            option_units.append(unit_data)
        else:
            elective_units.append(unit_data)
    
    # Sort all the lists so Level 1 units appear first, then Level 2, then Level 3
    # Within each level, sort alphabetically by unit code (ECON1101, ECON1102, etc.)
    core_units.sort(key=lambda x: (x['year_level'], x['code']))
    option_units.sort(key=lambda x: (x['year_level'], x['code']))
    elective_units.sort(key=lambda x: (x['year_level'], x['code']))
    
    # Combine all units for AI planning
    all_units_data = core_units + option_units + elective_units
    
    # Generate initial study plan using AI
    ai_result = ai_service.generate_study_plan(program_code, all_units_data)
    
    # Check if this is a valid plan vs an error
    plan_error = ai_result.get('error') if 'error' in ai_result else None
    plan_success = 'plan' in ai_result and 'reasoning' in ai_result
    
    # Don't validate the initial AI-generated plan - assume it's valid
    # Validation will only run when users modify the plan via AJAX
    validation_result = {'isValid': True, 'errors': [], 'warnings': []}
    
    return render_template('degree.html', 
                         degree_program=degree_program,
                         core_units=core_units,
                         option_units=option_units,
                         elective_units=elective_units,
                         all_units_data=all_units_data,
                         initial_plan=ai_result.get('plan', {}),
                         reasoning=ai_result.get('reasoning', ''),
                         plan_error=plan_error,
                         plan_success=plan_success,
                         validation_result=validation_result)

@bp.route('/api/validate_plan', methods=['POST'])
def validate_plan():
    """API endpoint to validate plan modifications"""
    try:
        data = request.get_json()
        program_code = data.get('program_code')  # Changed from course_code
        modified_plan = data.get('plan')
        
        if not program_code or not modified_plan:
            return jsonify({'error': 'Missing program_code or plan'}), 400
        
        # Get degree program units data
        degree_program = DegreeProgram.query.filter_by(code=program_code).first()
        if not degree_program:
            return jsonify({'error': 'Degree program not found'}), 404
        
        major_units = MajorUnit.query.filter_by(major_id=degree_program.major_id).join(Unit).all()
        units_data = []
        
        for major_unit in major_units:
            units_data.append({
                'code': major_unit.unit.code,
                'title': major_unit.unit.title,
                'prerequisites_raw': major_unit.unit.prerequisites_raw,
                'corequisites_raw': major_unit.unit.corequisites_raw,
                'availabilities_raw': major_unit.unit.availabilities_raw,
                'unit_type': major_unit.unit_type,
                'year_level': major_unit.year_level,
                'is_mandatory': major_unit.is_mandatory
            })
        
        # Validate using rule-based validation
        validation_result = ai_service.validate_plan_modification(modified_plan, units_data)
        
        return jsonify(validation_result)
        
    except Exception as e:
        logger.error(f"Error in validate_plan: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@bp.route('/api/export_pdf', methods=['POST'])
def export_pdf():
    """Export study plan to PDF"""
    try:
        data = request.get_json()
        program_code = data.get('program_code')  # Changed from course_code
        plan = data.get('plan')
        
        if not program_code or not plan:
            return jsonify({'error': 'Missing program_code or plan'}), 400
        
        degree_program = DegreeProgram.query.filter_by(code=program_code).first()
        if not degree_program:
            return jsonify({'error': 'Degree program not found'}), 404
        
        # Generate PDF (we'll need to update pdf_generator too)
        pdf_buffer = generate_study_plan_pdf(degree_program, plan)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_buffer.getvalue())
        temp_file.close()
        
        filename = f"study_plan_{program_code}.pdf"
        
        return send_file(temp_file.name, 
                        as_attachment=True, 
                        download_name=filename,
                        mimetype='application/pdf')
        
    except Exception as e:
        logger.error(f"Error in export_pdf: {str(e)}")
        return jsonify({'error': 'PDF generation failed'}), 500
    finally:
        # Clean up temp file
        try:
            os.unlink(temp_file.name)
        except:
            pass

@bp.route('/admin/import_status')
def import_status():
    """Admin page showing data import status"""
    from app.data_import import data_importer
    status = data_importer.get_import_status()
    return render_template('admin/import_status.html', status=status)

@bp.route('/admin/majors')
def admin_majors():
    """Admin page for managing majors"""
    from app.data_import import data_importer
    from app.models import Major, DegreeProgram
    
    # Get current majors
    current_majors = Major.query.all()
    
    # Get available majors from auto-discovery
    units_csv_path = 'Reference_Material/Data_from_Client/Units.csv'
    discovered_majors = data_importer.discover_major_mappings_from_csv(units_csv_path)
    
    # Format discovered majors for display
    available_majors = []
    for major_code, units_data in discovered_majors.items():
        total_units = len(units_data['core']) + len(units_data['option']) + len(units_data['bridging'])
        # Check if already exists
        existing_major = Major.query.filter_by(code=major_code).first()
        
        available_majors.append({
            'code': major_code,
            'title': data_importer._get_course_title_from_code(major_code),
            'total_units': total_units,
            'core_units': len(units_data['core']),
            'option_units': len(units_data['option']),
            'bridging_units': len(units_data['bridging']),
            'exists': existing_major is not None,
            'is_active': existing_major.is_active if existing_major else False
        })
    
    # Sort by code
    available_majors.sort(key=lambda x: x['code'])
    
    return render_template('admin/majors.html', 
                         current_majors=current_majors,
                         available_majors=available_majors)

@bp.route('/admin/majors/toggle/<major_code>', methods=['POST'])
def toggle_major(major_code):
    """Toggle major active status"""
    from app.data_import import data_importer
    
    major = Major.query.filter_by(code=major_code).first()
    
    if major:
        # Toggle existing major
        major.is_active = not major.is_active
        
        # Update degree program status
        for degree_program in major.degree_programs:
            degree_program.is_active = major.is_active
        
        db.session.commit()
        action = 'enabled' if major.is_active else 'disabled'
        
    else:
        # Create new major from discovery
        units_csv_path = 'Reference_Material/Data_from_Client/Units.csv'
        discovered_majors = data_importer.discover_major_mappings_from_csv(units_csv_path)
        
        if major_code in discovered_majors:
            major = data_importer.create_major_from_discovery(
                major_code, 
                discovered_majors[major_code], 
                enabled=True
            )
            if major:
                # Create degree program
                data_importer._create_degree_program(
                    major.bachelor_degree, 
                    major, 
                    f"BEC-{major_code.split('-')[1]}", 
                    f"{major.bachelor_degree.title}, {major.title}"
                )
                action = 'created and enabled'
            else:
                return jsonify({'error': 'Failed to create major'}), 500
        else:
            return jsonify({'error': 'Major not found in discovery data'}), 404
    
    return jsonify({'success': True, 'message': f'Major {major_code} {action}'})