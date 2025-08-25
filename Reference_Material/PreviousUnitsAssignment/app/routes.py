from app import controller
from app import app
from flask import render_template
from flask_login import current_user, login_user, logout_user, login_required # Flask-Login functions

# Create route for pages (aka views):

# This first one includes the control function, as it very simply renders the index.html page
# The rest pass the control logic to controller.py
@app.route('/')
@app.route('/index/')
def index():
    id = "index"
    return render_template('index.html', title_page="Home", class_page=id)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    return controller.login()

@app.route('/logout/')
def logout():
    return controller.logout()

@app.route('/history/')
@login_required
def history():
    return controller.history()

@app.route('/signup/', methods=['GET', 'POST'])
def signup():
    return controller.signup()

@app.route('/chat/', methods=["GET", "POST"])
@login_required
def chat():
    return controller.chat()


@app.route('/references/')
def references():
    id = "references"
    return render_template('references.html', title_page="References", class_page=id)