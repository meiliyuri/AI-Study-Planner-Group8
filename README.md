# AI Study Planner

An AI-powered Flask web application that helps university students plan their degree programs with intelligent study plan generation and prerequisite validation.

## Features

- **AI-Powered Plan Generation**: Uses Claude Opus to create valid study plans
- **Interactive Drag-and-Drop Interface**: Customize plans with real-time validation
- **Degree Rule Compliance**: Ensures all UWA Bachelor degree requirements are met
- **Major Support**: Currently supports Science and Economics degrees
- **Real-time Validation**: Immediate feedback on plan modifications
- **PDF Export**: Export completed plans for printing/sharing
- **Admin Panel**: Import new course data and manage the system

## Technology Stack

- **Backend**: Flask, SQLAlchemy, Claude API using the Opus 4.1 model
- **Frontend**: HTML, CSS, JavaScript, Bootstrap, SortableJS
- **Database**: SQLite (development), PostgreSQL (production)
- **AI Integration**: Claude Opus 4.1

## Project Structure

```bash
AI-Study-Planner-Group8
│   .env
│   .gitignore
│   app.py
│   check_prerequisites.py
│   CODE_OF_CONDUCT.md
│   data_loader.py
│   README.md
│   requirements.txt
│
├───app
│   │   controller.py
│   │   models.py
│   │   routes.py
│   │   __init__.py
│   │
│   ├───static
│   │   ├───css
│   │   │       contact.css
│   │   │       faq.css
│   │   │       home.css
│   │   │       planner.css
│   │   │       style.css
│   │   │
│   │   ├───images
│   │   │       uwa_logo.png
│   │   │
│   │   └───js
│   │           app.js
│   │
│   └───templates
│           admin.html
│           base.html
│           contact.html
│           faq.html
│           home.html
│           index.html
│           planner.html
│           settings.html
│
├───Reference_Material
│   └───Essential_Data
│           BP004 Bachelor of Science.pdf
│           BP013 Bachelor of Economics.pdf
│           MJD-AGBUS Agribusiness.pdf
│           MJD-AGSCI Agricultural Science.pdf
│           MJD-AGTEC Agricultural Technology.pdf
│           MJD-ECNPF Economics.pdf
│           MJD-FINEC Financial Economics.pdf
│           Sequence export (MJD-ECNPF).xlsx
│           Sequence export (MJD-FINEC).xlsx
│           Sequence export MJD-AGBUS.xlsx
│           Sequence export MJD-AGSCI.xlsx
│           Sequence export MJD-AGTEC.xlsx
│           Units with unit rules and availabilities.csv
│           Units.csv
│           XLSX_Structure_Analysis.md
│
└───tests
        conftest.py
        test_admin_db.py
        test_advanced.py
        test_basics.py
        test_planner.py
        test_faq.py
```

## Instructions to Run the app

1. **Pull code, create Python environment, activate & install pre-requisits**:

Windows:

```bash
git clone https://github.com/meiliyuri/AI-Study-Planner-Group8.git # pull repo
cd AI-Study-Planner-Group8

python3 -m venv venv # create environment and install requirements
.\venv\Scripts\Activate
pip install -r requirements.txt
pre-commit install # pre commit automation
```

macOS:

```bash
git clone https://github.com/meiliyuri/AI-Study-Planner-Group8.git # pull repo
cd AI-Study-Planner-Group8

python3 -m venv venv # create environment and install requirements
source venv/bin/activate
pip install -r requirements.txt
pre-commit install # pre commit automation
```

2. **Set a real API key**:

- If you are a team member: copy the **config.py** file from FILES in Teams in to the root of the project folder. Otherwise, contact the devoplement team for assistance.
- Important: **DO NOT** force syncing `config.py`(in `.gitignore` file already) to GitHub. It contains a real API key which will be deactivated if leaked.

3. **Initialise the DB and start the app**:

Run python data_loader.py **once** before the first launch to set up the database.

```bash
python data_loader.py
```

Run the flask app.

```bash
python -m flask run
```

![Run the flask app](https://github.com/user-attachments/assets/4688c0dd-c3fe-4080-bed2-ccc15d8c63c1)

4. **Visit**: <http://127.0.0.1:5000>

![Web Demo](https://github.com/user-attachments/assets/9cca92e0-1574-4b18-933b-ee7d65e316cb)

## FAQ

See the [FAQ page](http://127.0.0.1:5000/faq) in the web app for answers to common questions about speed, cost, accuracy, prerequisites, and exporting.

## Contact Page

If you encounter issues or have questions about the AI Study Planner, you can use the **Contact form** in the app:

* **Visit**: [http://127.0.0.1:5000/contact](http://127.0.0.1:5000/contact)
* Fill out the form with your **name**, **email**, and **message**.
* Submit your query, and the development team will review it.

This is the primary channel for reporting bugs, asking questions, or providing feedback while using the local development version of the app.

## Running Tests

To ensure everything is working correctly and all features are stable, the project includes automated tests for routes, the database, and planner functionality.

### 1. Activate the Python environment

Make sure you are in the project folder and your virtual environment is activated.

**Windows:**

```bash
.\venv\Scripts\Activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

### 2. Install test dependencies

All required packages are included in `requirements.txt`, including `pytest` and `beautifulsoup4` (for HTML parsing in tests). If you haven’t installed them yet:

```bash
pip install -r requirements.txt
```

### 3. Run the tests

From the project root folder, simply run:

```bash
pytest -v
```

* `-v` (verbose) shows each test’s status.
* All tests should pass.
* If any fail, carefully review the error message and make sure the environment is correctly set up.

### 4. Test coverage areas

* **Basic pages**: Home page, admin page, planner page.
* **Planner functionality**: Buttons, major selection, plan generation.
* **Admin panel and database**: Connection status, system badges.
* **Advanced features**: AI status badges, import logs, and validation messages.

<img width="1146" height="531" alt="image" src="https://github.com/user-attachments/assets/bb89ade4-a63b-4b4b-a333-6d9ad7d35f78" />

## Data Structure

### Bachelor Degree Requirements

- **Total Units**: 24 units (144 credit points)
- **Duration**: 6 semesters over 3 years
- **Level Distribution**:
  - Maximum 12 Level 1 units
  - Minimum 12 Level 2 or Level 3 units
  - Minimum 3 Level 3 units
- **Semester Load**: 4 units per semester

### Major Structure

Each major contains:

- **Mandatory units** (core): Must be completed
- **Optional units** (electives): Choose from available options
- **Bridging units**: Excluded from plans (CHEM1003, MATH1720, SCIE1500, ECON1111)

### Data Files

- `Units.csv`: Complete unit catalog with details
- `Units with unit rules and availabilities.csv`: Prerequisites and rules
- `Sequence export (MJD-*).xlsx`: Major-specific unit requirements

## AI Integration

### Plan Generation

Uses a multi-step AI pipeline:

1. **Initial Plan Generation**: Opus 4.1 creates a valid plan based on major requirements
2. **Real-Time Validation**: Some basic rules are checked (availability, prerequisits) immediately while units are being dragged around
2. **Quality of Service Check**: Opus 4.1 validates the bigger-picture of the plan using all available information

### Prompt Strategy

- **Generation Prompt**: Provides major requirements and asks for structured JSON plan
- **Validation Prompt**: Checks modifications against UWA degree rules
- **Temperature Settings**: Low temperature (0.1-0.3) for consistent, rule-based responses

### Future Enhancements & Known Issues

- BUG: AI Quality Check is missing the "or equivalent" part of the ECON1111 prerequisite
- Research: Not every Ai generated plan is compliant, look at ways to improve the success rate without moving more logic to the code
- Improvement: The plans must be cached to be cost effective, each call is 10-20c. Implement caching of base plans in to the DB.
- Improvement: Consider a two-stage build process which pipelines the first generation in to the Ai Validate Plan, and then re-generates the plan, to achieve a better percentage of valid outcomes. This may be part of the Research point above.
