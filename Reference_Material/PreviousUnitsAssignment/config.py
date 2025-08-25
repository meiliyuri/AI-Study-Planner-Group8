# Class to Store Configuration Variables
# Design pattern taken from Miguel Grinberg's Flask Mega-Tutorial

import os
basedir = os.path.abspath(os.path.dirname(__file__)) # Get the directory of the current file

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'MakeThisARealKeyInProduction'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False