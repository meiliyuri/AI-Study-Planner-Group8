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
            self.client = OpenAI(api_key=current_app.config['OPENAI_API_KEY'])
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

            # Format units for AI prompt
            units_text = self._format_units_for_prompt(units_data)

            prompt = f"""Generate a valid study plan for {course_code}.

# Units to Schedule:
{units_text}

Requirements:
- Standard workload is 4 units per semester
- All prerequisites must be met before scheduling a unit
- Core units should be prioritized
- Plan should span appropriate number of years
- Respect unit availability (if specified)

Respond with a JSON object in this format:
{{
    "plan": {{
        "Year 1, Semester 1": ["UNIT1", "UNIT2", "UNIT3", "UNIT4"],
        "Year 1, Semester 2": ["UNIT5", "UNIT6", "UNIT7", "UNIT8"],
        ...
    }},
    "reasoning": "Brief explanation of the plan logic"
}}"""

            response = client.chat.completions.create(
                model=current_app.config['OPENAI_MODEL'],
                temperature=current_app.config['OPENAI_TEMPERATURE'],
                max_tokens=current_app.config['OPENAI_MAX_TOKENS'],
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
        Validate a user's plan modification using AI
        
        Args:
            modified_plan (dict): The modified plan structure
            units_data (list): List of unit data for validation
            
        Returns:
            dict: Validation result with isValid and reasons
        """
        try:
            client = self._get_client()

            units_text = self._format_units_for_prompt(units_data)
            plan_text = self._format_plan_for_validation(modified_plan)

            prompt = f"""Validate the following study plan against the unit rules.

# Plan to Validate:
{plan_text}

# Unit Rules:
{units_text}

Check for:
- Prerequisites are met (prerequisite units scheduled in earlier semesters)
- No more than 4 units per semester
- Unit availability constraints (if specified)
- Corequisite requirements

Respond with JSON:
{{
    "isValid": true/false,
    "errors": ["list of specific validation errors"],
    "warnings": ["list of warnings or suggestions"]
}}"""

            response = client.chat.completions.create(
                model=current_app.config['OPENAI_MODEL'],
                temperature=0.1,  # Lower temperature for validation
                max_tokens=500,
                messages=[
                    {"role": "system", "content": "You are a strict academic rule validator. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ]
            )

            if response.choices:
                content = response.choices[0].message.content
                return self._parse_ai_response(content)

            return {"isValid": False, "errors": ["No response from AI validator"]}

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

# Global service instance
ai_service = AIStudyPlannerService()