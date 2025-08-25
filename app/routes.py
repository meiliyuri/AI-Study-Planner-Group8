from flask import Blueprint, render_template, request, jsonify, send_file
from app.models import Course, Unit, CourseUnit
from app.ai_service import ai_service
from app.pdf_generator import generate_study_plan_pdf
import logging
import tempfile
import os

logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Main page showing available courses"""
    courses = Course.query.all()
    return render_template('index.html', courses=courses)

@bp.route('/course/<course_code>')
def course_view(course_code):
    """Display course details and generate initial study plan"""
    course = Course.query.filter_by(code=course_code).first()
    if not course:
        return "Course not found", 404
    
    # Get units for this course
    course_units = CourseUnit.query.filter_by(course_id=course.id).join(Unit).all()
    units_data = []
    
    for course_unit in course_units:
        unit = course_unit.unit
        units_data.append({
            'code': unit.code,
            'title': unit.title,
            'prerequisites_raw': unit.prerequisites_raw,
            'corequisites_raw': unit.corequisites_raw,
            'credit_points': unit.credit_points,
            'unit_type': course_unit.unit_type
        })
    
    # Generate initial study plan using AI
    ai_result = ai_service.generate_study_plan(course_code, units_data)
    
    return render_template('course.html', 
                         course=course, 
                         units_data=units_data,
                         initial_plan=ai_result.get('plan', {}),
                         reasoning=ai_result.get('reasoning', ''))

@bp.route('/api/validate_plan', methods=['POST'])
def validate_plan():
    """API endpoint to validate plan modifications"""
    try:
        data = request.get_json()
        course_code = data.get('course_code')
        modified_plan = data.get('plan')
        
        if not course_code or not modified_plan:
            return jsonify({'error': 'Missing course_code or plan'}), 400
        
        # Get course units data
        course = Course.query.filter_by(code=course_code).first()
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        course_units = CourseUnit.query.filter_by(course_id=course.id).join(Unit).all()
        units_data = []
        
        for course_unit in course_units:
            unit = course_unit.unit
            units_data.append({
                'code': unit.code,
                'title': unit.title,
                'prerequisites_raw': unit.prerequisites_raw,
                'corequisites_raw': unit.corequisites_raw,
                'availabilities_raw': unit.availabilities_raw
            })
        
        # Validate using AI
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
        course_code = data.get('course_code')
        plan = data.get('plan')
        
        if not course_code or not plan:
            return jsonify({'error': 'Missing course_code or plan'}), 400
        
        course = Course.query.filter_by(code=course_code).first()
        if not course:
            return jsonify({'error': 'Course not found'}), 404
        
        # Generate PDF
        pdf_buffer = generate_study_plan_pdf(course, plan)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        temp_file.write(pdf_buffer.getvalue())
        temp_file.close()
        
        filename = f"study_plan_{course_code}.pdf"
        
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