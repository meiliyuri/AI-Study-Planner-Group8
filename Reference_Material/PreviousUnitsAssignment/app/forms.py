# Design pattern taken from Miguel Grinberg's Flask Mega-Tutorial
# Python classes to represent web forms. A form class defines the fields of the form as class variables.

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField,EmailField
from wtforms.validators import ValidationError, DataRequired, Email, EqualTo
from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(message="Username is required.")], description="Username must have at least 5 characters.")
    email = EmailField('Email', validators=[DataRequired(message="Email is required."), Email()])
    password = PasswordField('Password', validators=[DataRequired(message="Password is required.")], description="Password must have at least 6 characters; at least one letter and one number.")
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')
        if len(username.data) < 5:
            raise ValidationError('Username must have at least 5 characters.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

    def validate_password(self, password):
        if len(password.data) < 6:
            raise ValidationError('Password must have at least 6 characters.')
        if not any(char.isdigit() for char in password.data):
            raise ValidationError('Password must contain at least one number')
        if not any(char.isalpha() for char in password.data):
            raise ValidationError('Password must contain at least one letter')

class MessageForm(FlaskForm):
    content = StringField("What ingredients do you have?", validators=[DataRequired()])
    submit = SubmitField("Send")
