from datetime import datetime
from app import db, login
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

# Database models. Originally design patterns from Miguel's tutorial:

# User table, consisting of an ID, Username, Email, Password & a Foreign Key Constraint to Messages table
class User(UserMixin, db.Model): # UserMixin provides methods required by Flask-Login
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    Messages = db.relationship('Message', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User {}>'.format(self.username)
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Message table, consisting of an ID, the users message as Content, the AI's response as Response, a Timestamp & a Foreign Key Constraint to User table
class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(140))
    response = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Messages {}>'.format(self.body)

@login.user_loader # callback for Flask-Login
def load_user(id):
    return User.query.get(int(id))