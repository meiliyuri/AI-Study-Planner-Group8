import unittest
from flask import Flask
from flask_login import current_user, login_user, logout_user
from app import app, db
from app.models import User

# Tests to verify the pages exists
def test_index_page():
    with app.test_client() as client:
        response = client.get('/')
        #check if response is TRUE/show something in the page
        assert response.status_code==200
        #matching strings
        assert b'What Should I Cook' in response.data

def test_signup():
    with app.test_client() as client:
        response = client.get('/signup/')
        #check if response is TRUE/show something in the page
        assert response.status_code==200
        #matching strings
        assert b'Signup Page' in response.data

def test_login():
    with app.test_client() as client:
        response = client.get('/login/')
        #check if response is TRUE/show something in the page
        assert response.status_code==200
        #matching strings
        assert b'Sign In' in response.data

def test_references():
    with app.test_client() as client:
        response = client.get('/references/')
        #check if response is TRUE/show something in the page
        assert response.status_code==200
        #matching strings
        assert b'Miguel Grinberg' in response.data

def test_invalid_page(): # Checks invalid pages return the appropriate error
    with app.test_client() as client:
        response = client.get('/invalid_page')
        # Check if response is a 404 error
        assert response.status_code == 404

def test_chat():
    with app.test_client() as client:
        response = client.get('/chat/')
        # We are not logged in (yet) so this should return a 302, not 200
        assert response.status_code==302

def test_history():
    with app.test_client() as client:
        response = client.get('/history/')
        # We are not logged in (yet) so this should return a 302, not 200
        assert response.status_code==302

# These pages require auth to check, credit ChatGPT/StackOverflow for helping with session management
class TestHistoryPage(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_secure_pages(self):
        with app.test_request_context():
            with self.app as client:
                # Log in the user
                user = User.query.filter_by(username='testValid').first()
                login_user(user)
                # Make the request to the protected page, first History
                response = client.get('/history/')
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"History", response.data)
                #Make the request to the protected page, now Chat
                response = client.get('/chat/')
                self.assertEqual(response.status_code, 200)
                self.assertIn(b"Hi", response.data)