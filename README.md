# AI Study Planner

An AI-powered Flask web application that helps university students plan their degree programs with intelligent study plan generation and prerequisite validation.

## What It Does

This app helps students create study plans for university degrees by:
- **Showing available programs**: Currently tested with Bachelor of Economics majors (Economics, Financial Economics)
- **AI-generated plans**: Uses OpenAI to create smart 6-semester study plans considering prerequisites and year levels
- **Drag-and-drop editing**: Students can move units between semesters with real-time validation
- **PDF export**: Generate printable study plans
- **Admin interface**: Add/remove degree programs easily

## Quick Start for Microsoft Windows - instructions may vary for Linux & Macintosh

1. **Pull code, create Python environment, activate & install pre-requisits**:
   ```bash
   git clone -b ZacharyBaker3 https://github.com/meiliyuri/AI-Study-Planner-Group8.git
   cd AI-Study-Planner-Group8
   python3 -m venv venv
   .\venv\Scripts\Activate
   pip install -r requirements.txt
   ```
<img width="958" height="345" alt="Screenshot 2025-09-09 092748" src="https://github.com/user-attachments/assets/2d088ef3-a965-4c39-b9cc-78fa1f943222" />

<br></br>
2. **Set a real API key** (run once):
   ```bash
   copy config_local.py.template config_local.py
   ```
Modify in your chosen text editor, the real key is located in Teams FILES. It cannot and should not be pushed to Github, if it is OpenAi will immediately invalidate it.

<img width="958" height="323" alt="image" src="https://github.com/user-attachments/assets/16ff76bf-904a-4c2d-8434-68759aa271e8" />

3. **Initialise the DB and start the app**:
   ```bash
   python init_majors.py
   python -m flask run
   ```

<img width="958" height="487" alt="Screenshot 2025-09-09 093148" src="https://github.com/user-attachments/assets/79dee981-7457-46c4-b46d-ca6a77e51295" />


4. **Visit**: http://127.0.0.1:5000

<img width="1047" height="853" alt="image" src="https://github.com/user-attachments/assets/13a142cc-b17e-47f4-9e8b-464f96cb5d2b" />


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



