import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Claude AI API Key (dummy for local dev)
    CLAUDE_API_KEY = os.environ.get('CLAUDE_API_KEY', 'test-claude-key')

