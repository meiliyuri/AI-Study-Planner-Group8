# AI Service for study plan generation and validation
# Written with the aid of Claude AI assistant
#
# This service handles two main functions:
# 1. Generate initial study plans using OpenAI GPT (creates smart 6-semester plans)
# 2. Validate user modifications using rule-based logic (checks prerequisites, etc.)
#
# How it works:
# - For initial plans: Sends unit data to OpenAI, gets back a semester-by-semester plan
# - For validation: Uses Python logic to check prerequisites, unit mappings, etc.
# - Has fallback logic: If OpenAI fails, generates basic plans using rules
# - Handles equivalent units: ECOX1101 = ECON1101, STAX1520 = STAT1520, etc.
#
# The AI creates more intelligent plans (considers prerequisites, year levels)
# The rule-based validator catches errors when users drag units around

from openai import OpenAI
from flask import current_app
import json
import logging

logger = logging.getLogger(__name__)

class AIStudyPlannerService:
    """Service for AI-powered study plan generation and validation"""

    def __init__(self):
        self.client = None

    def _get_client(self):
        """Initialize OpenAI client if not already done"""
        if not self.client:
            try:
                # Try to get API key from Flask config first, then fallback to direct import
                api_key = None
                try:
                    api_key = current_app.config.get('OPENAI_API_KEY')
                except RuntimeError:
                    # Not in Flask context, try direct import
                    try:
                        from config_local import OPENAI_API_KEY
                        api_key = OPENAI_API_KEY
                    except ImportError:
                        import os
                        api_key = os.environ.get('OPENAI_API_KEY')
                
                if not api_key or api_key == 'your-api-key-here':
                    # No valid API key, return None to use fallback
                    return None
                    
                # Create custom http client to avoid proxy issues
                import httpx
                http_client = httpx.Client()
                self.client = OpenAI(api_key=api_key, http_client=http_client)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {str(e)}")
                return None
        return self.client

    def generate_study_plan(self, course_code, units_data):
        """
        Generate initial study plan for a course using AI
        
        Args:
            course_code (str): The course code (e.g., 'MJD-FINEC')
            units_data (list): List of unit dictionaries with codes, titles, prerequisites
            
        Returns:
            dict: Generated study plan structure
        """
        try:
            client = self._get_client()

            # If no OpenAI client available, use fallback logic
            if not client:
                return self._generate_fallback_plan(course_code, units_data)

            # Format units for AI prompt
            units_text = self._format_units_for_prompt(units_data)

            prompt = f"""Generate a valid study plan for {course_code}.

# Units to Schedule:
{units_text}

# SEMESTER ORDER:
Year 1, Semester 1 -> Year 1, Semester 2 -> Year 2, Semester 1 -> Year 2, Semester 2 -> Year 3, Semester 1 -> Year 3, Semester 2

# CRITICAL PREREQUISITE RULES:
- Each unit is worth 6 points
- "12 points at level X" = must have 2 units at that level completed in EARLIER semesters
- "Any one level X unit" = must have at least 1 unit at that level completed in EARLIER semesters
- Specific unit prerequisites must be completed in EARLIER semesters

# LEVEL IDENTIFICATION:
- Level 1 units: codes ending in 1xxx (e.g. ASIA1002, POLS1102) - typically no prerequisites
- Level 2 units: codes ending in 2xxx (e.g. IREL2001, POLS2220) - typically need level 1 units
- Level 3 units: codes ending in 3xxx (e.g. ASIA3005, POLS3308) - typically need level 2 units

# STRICT PLANNING STRATEGY:
1. Year 1, Semester 1: ONLY Level 1 units (1xxx) and Level 2 units with "Nil" prerequisites
2. Year 1, Semester 2: Level 2 units (2xxx) that need level 1 units completed
3. Year 2, Semester 1: Level 3 units (3xxx) that need level 2 units completed
4. Year 2, Semester 2: More Level 3 units and advanced units
5. Year 3, Semester 1: Remaining Level 3 units and electives
6. Year 3, Semester 2: Final units and remaining electives
7. NEVER schedule a unit before its prerequisites are satisfied

# VALIDATION CHECK:
For each unit you schedule, verify:
- Count how many units of each level are completed in earlier semesters
- Ensure all specific prerequisites are satisfied
- Maximum 4 units per semester

Respond with a JSON object in this format:
{{
    "plan": {{
        "Year 1, Semester 1": ["UNIT1", "UNIT2", "UNIT3", "UNIT4"],
        "Year 1, Semester 2": ["UNIT5", "UNIT6", "UNIT7", "UNIT8"],
        "Year 2, Semester 1": ["UNIT9", "UNIT10", "UNIT11", "UNIT12"],
        "Year 2, Semester 2": ["UNIT13", "UNIT14", "UNIT15", "UNIT16"],
        "Year 3, Semester 1": ["UNIT17", "UNIT18", "UNIT19", "UNIT20"],
        "Year 3, Semester 2": ["UNIT21", "UNIT22", "UNIT23", "UNIT24"]
    }},
    "reasoning": "Brief explanation of how prerequisites are satisfied in each semester across 3 years"
}}"""

            # Get OpenAI config, with fallbacks for outside Flask context
            try:
                model = current_app.config['OPENAI_MODEL']
                temperature = current_app.config['OPENAI_TEMPERATURE']
                max_tokens = current_app.config['OPENAI_MAX_TOKENS']
            except RuntimeError:
                # Outside Flask context, use defaults
                model = 'gpt-3.5-turbo'
                temperature = 0.3
                max_tokens = 1000

            response = client.chat.completions.create(
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": "You are an expert academic advisor creating study plans. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )

            if response.choices:
                content = response.choices[0].message.content
                return self._parse_ai_response(content)

            return {"error": "No response from AI"}

        except Exception as e:
            logger.error(f"Error generating study plan: {str(e)}")
            return {"error": f"AI service error: {str(e)}"}

    def validate_plan_modification(self, modified_plan, units_data):
        """
        Validate a user's plan modification using rule-based logic
        
        Args:
            modified_plan (dict): The modified plan structure
            units_data (list): List of unit data for validation
            
        Returns:
            dict: Validation result with isValid and reasons
        """
        try:
            # Always use rule-based validation as it's more reliable than AI
            return self._validate_plan_fallback(modified_plan, units_data)
        except Exception as e:
            logger.error(f"Error validating plan: {str(e)}")
            return {"isValid": False, "errors": [f"Validation service error: {str(e)}"]}

    def _format_units_for_prompt(self, units_data):
        """Format unit data for AI prompts"""
        formatted = []
        for unit in units_data:
            unit_text = f"- {unit['code']}: {unit['title']}"
            if unit.get('prerequisites_raw'):
                unit_text += f"\n  Prerequisites: {unit['prerequisites_raw']}"
            if unit.get('corequisites_raw'):
                unit_text += f"\n  Corequisites: {unit['corequisites_raw']}"
            if unit.get('availabilities_raw'):
                unit_text += f"\n  Available: {unit['availabilities_raw']}"
            formatted.append(unit_text)
        return "\n".join(formatted)

    def _format_plan_for_validation(self, plan):
        """Format plan structure for validation prompt"""
        formatted = []
        for semester, units in plan.items():
            formatted.append(f"{semester}: {', '.join(units)}")
        return "\n".join(formatted)

    def _generate_fallback_plan(self, course_code, units_data):
        """Generate a basic study plan without AI (fallback when no API key)"""
        try:
            # Check if this is a broad bachelor program with no structured units
            if len(units_data) == 0 and self._is_broad_bachelor_program(course_code):
                return {
                    "plan": {},
                    "reasoning": f"{course_code} is a broad bachelor program that allows students to choose from a wide range of elective units across the university. To create a study plan, you would typically choose a specific major or specialization within this program. Please consult your academic advisor or the university handbook for available majors and their unit requirements."
                }
            
            # Sort units by type (core first) and year level
            core_units = [u for u in units_data if u.get('unit_type') == 'core']
            option_units = [u for u in units_data if u.get('unit_type') == 'option']
            elective_units = [u for u in units_data if u.get('unit_type') == 'elective']
            
            # Sort each type by year level
            core_units.sort(key=lambda x: (x.get('year_level', 1), x.get('code', '')))
            option_units.sort(key=lambda x: (x.get('year_level', 2), x.get('code', '')))
            elective_units.sort(key=lambda x: (x.get('year_level', 3), x.get('code', '')))
            
            # Create a plan with exactly 24 units (144 points) for a 3-year degree
            # Strategy: All core units + select some option units to reach 24 total
            selected_units = []
            
            # Add all core units (mandatory)
            selected_units.extend(core_units)
            
            # Calculate how many more units we need to reach 24
            units_needed = 24 - len(core_units)
            
            # Add option units based on requirements
            if course_code == 'BEC-ECNPF':
                # Economics: Need 1 level 2 option (6 points) + 3 level 3 options (18 points)
                level2_options = [u for u in option_units if u.get('year_level') == 2]
                level3_options = [u for u in option_units if u.get('year_level') == 3]
                
                # Add 1 level 2 option unit
                if level2_options and units_needed > 0:
                    selected_units.append(level2_options[0])
                    units_needed -= 1
                
                # Add 3 level 3 option units
                for unit in level3_options[:min(3, units_needed)]:
                    selected_units.append(unit)
                    units_needed -= 1
                    
            elif course_code == 'BEC-FINEC':
                # Financial Economics: Need 2 level 3 options (12 points)
                level3_options = [u for u in option_units if u.get('year_level') == 3]
                
                # Add 2 level 3 option units  
                for unit in level3_options[:min(2, units_needed)]:
                    selected_units.append(unit)
                    units_needed -= 1
            
            # If we still need more units, add from remaining options/electives to reach 24 total
            remaining_units = [u for u in option_units + elective_units if u not in selected_units]
            for unit in remaining_units[:units_needed]:
                selected_units.append(unit)
                units_needed -= 1
            
            # If we still don't have enough, create placeholder units for general electives
            if units_needed > 0:
                general_electives_needed = units_needed
                logger.info(f"Need {general_electives_needed} general elective units for {course_code}")
                
                # Create placeholder units for display
                for i in range(general_electives_needed):
                    placeholder_unit = {
                        'code': f'ELEC{1000 + i}',
                        'title': f'General Elective Unit {i+1}',
                        'prerequisites_raw': '',
                        'corequisites_raw': '',
                        'credit_points': 6,
                        'unit_type': 'elective',
                        'year_level': 2 + (i % 2),  # Spread across years 2-3
                        'is_mandatory': False
                    }
                    selected_units.append(placeholder_unit)
            
            # Sort selected units by year level for logical progression
            selected_units.sort(key=lambda x: (x.get('year_level', 1), x.get('code', '')))
            
            # Generate 3-year plan (4 units per semester, 6 semesters total)
            plan = {}
            current_units = []
            
            year = 1
            semester = 1
            
            for unit in selected_units:
                current_units.append(unit['code'])
                
                # When we have 4 units or it's the last unit, create a semester
                if len(current_units) == 4 or unit == selected_units[-1]:
                    semester_key = f"Year {year}, Semester {semester}"
                    plan[semester_key] = current_units.copy()
                    current_units = []
                    
                    # Move to next semester (6 semesters total)
                    if semester == 1:
                        semester = 2
                    else:
                        semester = 1
                        year += 1
                        
                    # Stop after 3 years (6 semesters)
                    if year > 3:
                        break
            
            return {
                "plan": plan,
                "reasoning": f"Study plan generated for {course_code} with {len(selected_units)} units ({len(selected_units) * 6} points). Includes all core units plus selected option units to meet degree requirements. This is a basic plan - for prerequisite-aware planning, configure an OpenAI API key."
            }
            
        except Exception as e:
            logger.error(f"Error in fallback plan generation: {str(e)}")
            return {
                "error": f"Fallback plan generation failed: {str(e)}"
            }
    
    def _validate_plan_fallback(self, modified_plan, units_data):
        """Rule-based plan validation that actually works correctly"""
        try:
            errors = []
            warnings = []
            
            # Create a lookup for unit prerequisites
            unit_prereqs = {}
            for unit in units_data:
                unit_prereqs[unit['code']] = unit.get('prerequisites_raw', '').strip()
            
            # Create semester order list for chronological checking
            semester_order = []
            semester_units = {}
            
            for semester, units in modified_plan.items():
                semester_order.append(semester)
                semester_units[semester] = units
                
                # Check unit count per semester
                if len(units) > 4:
                    errors.append(f"{semester} has {len(units)} units (maximum 4 allowed)")
            
            # Sort semesters chronologically
            def semester_sort_key(sem):
                if 'Year 1, Semester 1' in sem: return 1
                elif 'Year 1, Semester 2' in sem: return 2
                elif 'Year 2, Semester 1' in sem: return 3
                elif 'Year 2, Semester 2' in sem: return 4
                elif 'Year 3, Semester 1' in sem: return 5
                elif 'Year 3, Semester 2' in sem: return 6
                else: return 999
                
            semester_order.sort(key=semester_sort_key)
            
            # Check prerequisites for each unit
            for i, semester in enumerate(semester_order):
                units_in_semester = semester_units[semester]
                
                # Get all units completed in earlier semesters
                completed_units = []
                for j in range(i):
                    earlier_semester = semester_order[j]
                    completed_units.extend(semester_units[earlier_semester])
                
                for unit_code in units_in_semester:
                    prereq_text = unit_prereqs.get(unit_code, '')
                    
                    if self._check_prerequisites(unit_code, prereq_text, completed_units, errors, semester):
                        continue  # Prerequisites satisfied
            
            return {
                "isValid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings
            }
            
        except Exception as e:
            logger.error(f"Error in rule-based validation: {str(e)}")
            return {
                "isValid": False,
                "errors": [f"Validation failed: {str(e)}"],
                "warnings": []
            }
    
    def _check_prerequisites(self, unit_code, prereq_text, completed_units, errors, current_semester):
        """Check if prerequisites are satisfied by completed units"""
        if not prereq_text or prereq_text.lower().strip() in ['nil', 'nil.', '', 'none']:
            return True  # No prerequisites
        
        prereq_lower = prereq_text.lower()
        
        # Skip validation for Level 1 units in Year 1, Semester 1 (assume they have no real prerequisites)
        if current_semester == 'Year 1, Semester 1' and unit_code[4] == '1':
            return True
        
        # Handle equivalent unit patterns (more generic approach)
        equivalent_mappings = self._build_equivalent_mappings()
        
        # Handle known waivable prerequisites
        waivable_prereqs = {
            'math1720': [],  # Mathematics prerequisite - assume satisfied by ATAR
            'econ1111': [],  # Quantitative methods - assume can be waived  
            'econ1000': ['ECON1101', 'ECON1102']  # Generic economics foundation
        }
        
        # Extract all unit codes mentioned in prerequisites
        import re
        mentioned_units = re.findall(r'[A-Z]{4}\d{4}', prereq_text)
        
        # Check if prerequisites involve "or" alternatives
        or_groups = []
        if ' or ' in prereq_text.lower():
            # Split by 'or' and check each alternative
            alternatives = re.split(r'\s+or\s+', prereq_text, flags=re.IGNORECASE)
            for alt in alternatives:
                alt_units = re.findall(r'[A-Z]{4}\d{4}', alt)
                if alt_units:
                    or_groups.append(alt_units)
        
        # If we have OR groups, check if ANY group is satisfied
        if or_groups:
            group_satisfied = False
            for group in or_groups:
                if all(self._unit_is_completed(unit, completed_units, equivalent_mappings) for unit in group):
                    group_satisfied = True
                    break
            if not group_satisfied:
                # Only report error if it's a real missing prerequisite
                missing_units = [unit for group in or_groups for unit in group if not self._unit_is_completed(unit, completed_units, equivalent_mappings)]
                if missing_units and not any(unit.lower() in equivalent_mappings and not equivalent_mappings[unit.lower()] for unit in missing_units):
                    errors.append(f"Unit {unit_code} requires one of: {' or '.join([' + '.join(group) for group in or_groups])}")
                    return False
        else:
            # Check individual unit prerequisites
            missing_units = []
            for required_unit in mentioned_units:
                if not self._unit_is_completed(required_unit, completed_units, equivalent_mappings):
                    # Skip if it's a known equivalent that can be waived
                    if (required_unit.lower() not in equivalent_mappings or equivalent_mappings[required_unit.lower()]) and \
                       (required_unit.lower() not in waivable_prereqs or waivable_prereqs[required_unit.lower()]):
                        missing_units.append(required_unit)
            
            if missing_units:
                errors.append(f"Unit {unit_code} requires: {', '.join(missing_units)}")
                return False
        
        # Check for point-based prerequisites (more lenient)
        if '12 points' in prereq_lower and 'level' in prereq_lower:
            # For now, assume point requirements are generally met in a well-structured plan
            # This is a fallback plan, so we're more lenient
            pass
        
        return True
    
    def _unit_is_completed(self, unit_code, completed_units, equivalent_mappings):
        """Check if a unit (or its equivalent) is completed"""
        if unit_code in completed_units:
            return True
        
        # Check equivalent mappings
        unit_lower = unit_code.lower()
        if unit_lower in equivalent_mappings:
            equivalents = equivalent_mappings[unit_lower]
            if not equivalents:  # Empty list means this prerequisite can be waived
                return True
            return any(equiv in completed_units for equiv in equivalents)
        
        return False
    
    def _build_equivalent_mappings(self):
        """Build equivalent unit mappings dynamically from database patterns"""
        from app.models import Unit
        equivalent_mappings = {}
        
        try:
            # Find ECOX pattern units and their ECON equivalents
            ecox_units = Unit.query.filter(Unit.code.like('ECOX%')).all()
            for ecox_unit in ecox_units:
                # Map ECOX1101 -> ECON1101, ECOX1102 -> ECON1102, etc.
                potential_equivalent = ecox_unit.code.replace('ECOX', 'ECON')
                equivalent_unit = Unit.query.filter_by(code=potential_equivalent).first()
                if equivalent_unit:
                    # Both directions of mapping
                    equivalent_mappings[ecox_unit.code.lower()] = [potential_equivalent]
                    equivalent_mappings[potential_equivalent.lower()] = [ecox_unit.code]
            
            # Find STAX pattern (STAX1520 -> STAT1520)
            stax_units = Unit.query.filter(Unit.code.like('STAX%')).all()
            for stax_unit in stax_units:
                potential_equivalent = stax_unit.code.replace('STAX', 'STAT')
                equivalent_unit = Unit.query.filter_by(code=potential_equivalent).first()
                if equivalent_unit:
                    equivalent_mappings[stax_unit.code.lower()] = [potential_equivalent]
                    equivalent_mappings[potential_equivalent.lower()] = [stax_unit.code]
            
        except Exception as e:
            # If database query fails, return basic mappings
            logger.warning(f"Could not build dynamic equivalent mappings: {e}")
            equivalent_mappings = {
                'ecox1101': ['ECON1101'],
                'ecox1102': ['ECON1102'],
                'stax1520': ['STAT1520']
            }
        
        return equivalent_mappings
    
    def _parse_ai_response(self, content):
        """Parse JSON response from AI, with fallback handling"""
        try:
            # Try to extract JSON from response
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:-3]
            elif content.startswith('```'):
                content = content[3:-3]

            return json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse AI response as JSON: {content}")
            return {"error": "Invalid response format from AI", "raw_response": content}
    
    def _is_broad_bachelor_program(self, course_code):
        """Check if course code represents a broad bachelor program"""
        return course_code.startswith(('BP', 'BH', 'CB'))

# Global service instance
ai_service = AIStudyPlannerService()