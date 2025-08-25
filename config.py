import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///study_planner.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # OpenAI Configuration
    OPENAI_API_KEY = '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'
    OPENAI_MODEL = 'gpt-3.5-turbo'
    OPENAI_TEMPERATURE = 0.3  # Lower temperature for more consistent rule interpretation
    OPENAI_MAX_TOKENS = 1000