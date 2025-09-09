# AI Study Planner

An AI-powered Flask web application that helps university students plan their degree programs with intelligent study plan generation and prerequisite validation.

## What It Does

This app helps students create study plans for university degrees by:
- **Showing available programs**: Currently supports Bachelor of Economics majors (Economics, Financial Economics)
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
  - Shows available degree programs (Economics, Financial Economics)
  - Select your program to start planning

- **Study Plan Generation**: http://127.0.0.1:5000/degree/BEC-ECNPF
  - AI-generated 6-semester study plan
  - Drag-and-drop interface to modify plan
  - Real-time prerequisite validation
  - PDF export functionality

- **Financial Economics Program**: http://127.0.0.1:5000/degree/BEC-FINEC
  - Alternative major with different unit requirements
  - Same AI planning and validation features

### Admin Functions
- **Import Status**: http://127.0.0.1:5000/admin/import_status
  - Shows database statistics
  - View imported units and majors count
  - System health check

- **Manage Majors**: http://127.0.0.1:5000/admin/majors
  - Enable/disable degree programs
  - Add new majors from CSV data
  - View unit breakdown per major

### API Endpoints (used by JavaScript)
- **Plan Validation**: POST to /api/validate_plan
- **PDF Export**: POST to /api/export_pdf

## Current Status

---

## 2️⃣ Project Resources

### 📂 GitHub Repository
[AI Study Planner GitHub Link](https://github.com/meiliyuri/AI-Study-Planner-Group8.git)

### 📌 Jira Board
[Jira Project Board Link](https://cits5206-2025s2-gourp8.atlassian.net/jira/software/projects/ASP/summary)

### 💬 MS Teams Project Area
[MS Teams Link](https://teams.microsoft.com/l/channel/19%3A878c9bc400744c2388c6fddd909a99eb%40thread.tacv2/Group%208?groupId=e524efef-b404-40f0-a05e-8dd542306098&tenantId=05894af0-cb28-46d8-8716-74cdb46e2226&ngc=true)

### 📝 Meeting Minutes
[Meeting Minutes SharePoint Folder](https://uniwa.sharepoint.com/:f:/r/teams/CITS5206SEM-22025-Group8/Shared%20Documents/Group%208/Meeting%20Minutes?csf=1&web=1&e=2pU9t4)

### 📅 Project Specification and Plans
[Project Specification and Plans Document](https://uniwa.sharepoint.com/:w:/r/teams/CITS5206SEM-22025-Group8/Shared%20Documents/Group%208/2025-08-03%20-%20Project%20Specification%20and%20Plans%20(Ai%20First%20DRAFT).docx?d=w07de8b6aa1964b9790ed4f46c9dc61c0&csf=1&web=1&e=p3Awge)

---

## 3️⃣ Repository Structure
```plaintext
AI-Study-Planner-Group8/
├── .gitignore
├── README.md
├── Project-Plan/
├── Meeting-Notes/
├── src/
└── resources/
