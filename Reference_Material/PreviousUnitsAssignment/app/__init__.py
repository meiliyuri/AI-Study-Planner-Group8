from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate # We need this library for db operations, this works so no need to change but we're unlikely to need to use the migration function
from flask_login import LoginManager

app = Flask(__name__) # Initialise the app
app.config.from_object(Config) # Load the config file
db = SQLAlchemy(app) # Initialise the database
migrate = Migrate(app, db) # Initialise the migration function
app.debug = True
login = LoginManager(app) # Initialise the login manager
login.login_view = 'login' # Used to re-direct unauth'd users who try to access the chat page through to the login page

from app import routes, models, forms, controller