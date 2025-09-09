# AI Study Planner

An AI-powered Flask web application that helps university students plan their degree programs with intelligent study plan generation and prerequisite validation.

## What It Does

This app helps students create study plans for university degrees by:
- **Showing available programs**: Currently tested with Bachelor of Economics majors (Economics, Financial Economics)
- **AI-generated plans**: Uses OpenAI to create smart 6-semester study plans considering prerequisites and year levels
- **Drag-and-drop editing**: Students can move units between semesters with real-time validation
- **PDF export**: Generate printable study plans
- **Admin interface**: Add/remove degree programs easily

## Quick Start

1. **Install dependencies**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Setup database** (run once):
   ```bash
   python init_majors.py
   ```

3. **Run the app**:
   ```bash
   python -m flask run
   ```

4. **Visit**: http://127.0.0.1:5000

## Application URLs and Functions

After running the app, you can access these main features:

### Main User Functions
- **Homepage**: http://127.0.0.1:5000/
### Admin Functions
- **Import Status**: http://127.0.0.1:5000/admin/import_status
- **Manage Majors**: http://127.0.0.1:5000/admin/majors
### API Endpoints (used by JavaScript)
- **Plan Validation**: POST to /api/validate_plan
- **PDF Export**: POST to /api/export_pdf

## 3️⃣ Repository Structure
```plaintext
AI-Study-Planner-Group8/
├── .gitignore
├── README.md
├── Project-Plan/
├── Meeting-Notes/
├── src/
└── resources/

