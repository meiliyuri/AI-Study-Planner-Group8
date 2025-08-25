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