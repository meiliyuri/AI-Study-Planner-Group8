# Flask Application Factory for AI Study Planner
# Written with the aid of Claude AI assistant
#
# This file creates and configures the Flask application instance.
# It sets up the database, registers blueprints, and configures the app.

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# Initialize SQLAlchemy (database ORM)
db = SQLAlchemy()

def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Basic Flask configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Database configuration - SQLite database stored in instance folder
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///study_planner.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # OpenAI API configuration
    try:
        # Try to import from local config file first
        from config_local import OPENAI_API_KEY
        app.config['OPENAI_API_KEY'] = OPENAI_API_KEY
    except ImportError:
        # Fall back to environment variable
        app.config['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'your-api-key-here')
    
    # OpenAI model settings
    app.config['OPENAI_MODEL'] = 'gpt-3.5-turbo'
    app.config['OPENAI_TEMPERATURE'] = 0.3
    app.config['OPENAI_MAX_TOKENS'] = 1000
    
    # Initialize database with app
    db.init_app(app)
    
    # Register blueprints (route handlers)
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)
    
    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()
    
    return app