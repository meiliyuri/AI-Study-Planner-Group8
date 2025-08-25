from app import app, db
from app.forms import RegistrationForm, LoginForm
from wtforms.validators import ValidationError
from app.models import User
import pytest

#REGISTER
user_test = "testUser"

#test response for to register user
def test_registration_form(client):    
    with app.app_context():
        client.get('/signup/')

        # Get the CSRF token from the form
        form = RegistrationForm()
        csrf_token = form.csrf_token.current_token

        # Make the second client request with the CSRF token included
        form_data = {
            'username': user_test,
            'email': user_test+'@example.com',
            'password': 'password123',
            'password2': 'password123',
            'csrf_token': csrf_token
        }     
        print(User.query.all())
        response = client.post('/signup/', data=form_data, follow_redirects=True)
        assert response.status_code == 200

#test if user was created in the DB
def test_user_db_check(client): 
    with app.app_context():
        client.get('/signup/')
        # Ensure user was added to the database
        user = User.query.filter_by(username=user_test).first()
        assert user is not None

        #delete user after test
        db.session.delete(user)
        db.session.commit()

#test create a duplicated user
#delete the duplicated user after test
def test_user_already_exists(client):   
    with app.app_context():      
        client.get('/signup/')
        user = User(username='testDuplicated', email='testDuplicated@example.com',)
        db.session.add(user)
        db.session.commit()

        form = RegistrationForm(username='testDuplicated', email='testDuplicated@example.com', password='password123', password2='password123')
        assert form.validate() == False

        db.session.delete(user)
        db.session.commit()

def test_user_already_exists_email(client):   
    with app.app_context():      
        client.get('/signup/')
        user = User(username='testDuplicated', email='testDuplicatedEmail@example.com',)
        db.session.add(user)
        db.session.commit()

        form = RegistrationForm(username='testDuplicated', email='testDuplicatedEmail@example.com', password='password123', password2='password123')
        assert form.validate() == False
        assert 'Please use a different email address.' in form.email.errors

        db.session.delete(user)
        db.session.commit()

def test_user_already_exists_usernme(client):   
    with app.app_context():      
        client.get('/signup/')
        user = User(username='testDuplicatedUser', email='testDuplicatedEmail@example.com',)
        db.session.add(user)
        db.session.commit()

        form = RegistrationForm(username='testDuplicatedUser', email='testDuplicated@example.com', password='password123', password2='password123')
        assert form.validate() == False
        assert 'Please use a different username.' in form.username.errors

        db.session.delete(user)
        db.session.commit()

#user required
def test_user_required(client): 
    with app.app_context():
        client.get('/signup/')        
        form = RegistrationForm(username='')
        assert form.validate() == False
        assert 'Username is required.' in form.username.errors

def test_user_lenght(client): 
    with app.app_context():
        client.get('/signup/')        
        form = RegistrationForm(username='123')
        assert form.validate() == False
        assert 'Username must have at least 5 characters.' in form.username.errors

#email required
def test_email_required(client): 
    with app.app_context():
        client.get('/signup/')        
        form = RegistrationForm(email='')
        assert form.validate() == False
        assert 'Email is required.' in form.email.errors

#password required
def test_password_required(client): 
    with app.app_context():
        client.get('/signup/')        
        form = RegistrationForm(password='')
        assert form.validate() == False
        assert 'Password is required.' in form.password.errors

def test_password_lenght(client): 
    with app.app_context():
        client.get('/signup/')        
        form = RegistrationForm(password='123')
        assert form.validate() == False
        assert 'Password must have at least 6 characters.' in form.password.errors

def test_password_only_letters(client): 
    with app.app_context():
        client.get('/signup/')        
        form = RegistrationForm(password='aabcdefg')
        assert form.validate() == False
        assert 'Password must contain at least one number' in form.password.errors

def test_password_only_numbers(client): 
    with app.app_context():
        client.get('/signup/')        
        form = RegistrationForm(password='12345678')
        assert form.validate() == False
        assert 'Password must contain at least one letter' in form.password.errors


##LOGIN
#test form
def test_login(client):       
    with app.app_context():
        client.get('/login/')  
        form_data = LoginForm(
            username="testUser",
            password="testUser1"
        )
        assert form_data.username.data == "testUser"
        assert form_data.password.data == "testUser1"

#test login
#need to provide a valid user
def test_login(client):
    with app.app_context():
    # Navigate to the login page
        response = client.get('/login/')
        assert response.status_code == 200

        # Log in with valid credentials
        response = client.post('/login/', data={'username': 'testValid', 'password': '123456A'}, follow_redirects=True)
        print(response.data)
        assert response.status_code == 200