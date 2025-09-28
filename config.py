import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key")
    # use one file for both the web app and data_loader.py
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        f"sqlite:///{os.path.join(BASE_DIR, 'studyplanner.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "dummy-local-key")

