# PDF Generator for Study Plans
# Written with the aid of Claude AI assistant
#
# This module generates PDF versions of study plans using ReportLab.
# It creates nicely formatted PDFs showing the semester-by-semester plan.

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from io import BytesIO
import logging

logger = logging.getLogger(__name__)

def generate_study_plan_pdf(degree_program, plan_data):
    """
    Generate a PDF document for a study plan
    
    Args:
        degree_program: DegreeProgram object containing program details
        plan_data: Dictionary containing the study plan structure
        
    Returns:
        BytesIO: Buffer containing the PDF data
    """
    try:
        # Create a buffer to store PDF data
        buffer = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # Get standard styles
        styles = getSampleStyleSheet()
        story = []
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        title = Paragraph(f"Study Plan: {degree_program.display_title}", title_style)
        story.append(title)
        story.append(Spacer(1, 12))
        
        # Program information
        info_style = styles['Normal']
        info_text = f"""
        <b>Program Code:</b> {degree_program.code}<br/>
        <b>Degree:</b> {degree_program.bachelor_degree.title}<br/>
        <b>Major:</b> {degree_program.major.title}<br/>
        <b>Duration:</b> {degree_program.bachelor_degree.duration_years} years<br/>
        <b>Total Credit Points:</b> {degree_program.bachelor_degree.total_credit_points}
        """
        
        info_para = Paragraph(info_text, info_style)
        story.append(info_para)
        story.append(Spacer(1, 20))
        
        # Study plan table
        if plan_data:
            # Create table data
            table_data = []
            table_data.append(['Semester', 'Units'])  # Header
            
            # Sort semesters chronologically
            semester_order = [
                'Year 1, Semester 1', 'Year 1, Semester 2',
                'Year 2, Semester 1', 'Year 2, Semester 2', 
                'Year 3, Semester 1', 'Year 3, Semester 2'
            ]
            
            for semester in semester_order:
                if semester in plan_data:
                    units = plan_data[semester]
                    if units:
                        units_text = '<br/>'.join(units)
                        table_data.append([semester, units_text])
            
            # Create table
            table = Table(table_data, colWidths=[2*inch, 4*inch])
            
            # Style the table
            table.setStyle(TableStyle([
                # Header style
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                
                # Data style
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                
                # Alternating row colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            
            story.append(table)
        else:
            # No plan data available
            no_plan_text = "No structured study plan available for this program."
            no_plan_para = Paragraph(no_plan_text, styles['Normal'])
            story.append(no_plan_para)
        
        story.append(Spacer(1, 20))
        
        # Footer note
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey
        )
        
        footer_text = """
        <b>Important Notes:</b><br/>
        • This study plan is generated for planning purposes only<br/>
        • Please consult with academic advisors before finalizing your enrollment<br/>
        • Prerequisites and unit availability may change<br/>
        • Generated by AI Study Planner
        """
        
        footer_para = Paragraph(footer_text, footer_style)
        story.append(footer_para)
        
        # Build PDF
        doc.build(story)
        
        # Return the buffer
        buffer.seek(0)
        return buffer
        
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise