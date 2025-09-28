# config.py
import os
from dotenv import load_dotenv

# Load .env (if present) into environment variables
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f"sqlite:///{os.path.join(BASE_DIR, 'studyplanner.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # API keys must come from environment variables (no hardcoded fallbacks)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')   # may be None
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY')   # must be set for production
