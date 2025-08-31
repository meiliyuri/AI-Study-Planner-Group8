import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///study_planner.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenAI Configuration
    try:
        from config_local import OPENAI_API_KEY
        OPENAI_API_KEY = OPENAI_API_KEY
    except ImportError:
        OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY') or 'your-api-key-here'
    OPENAI_MODEL = 'gpt-3.5-turbo'
    OPENAI_TEMPERATURE = 0.3  # Lower temperature for more consistent rule interpretation
    OPENAI_MAX_TOKENS = 1000