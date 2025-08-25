from app import app, db
from flask import Flask, render_template, request, flash, redirect, url_for, request
from markupsafe import escape, Markup
from app.forms import LoginForm, RegistrationForm, MessageForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Message
from werkzeug.urls import url_parse # used to re-direct back after successful login
from openai import OpenAI

client = OpenAI(api_key='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')

# Controller functions for the routes, to keep the routes.py file clean
# Attributions: Original design pattern from Miguel's tutorial, modified to suit our needs
# Written with the aid of Ai toolsets such as GitHub CoPilot & ChatGPT

# OpenAI API credentials, required for API calls later (user: z*******@gmail.com)

def login(): # Login function, accepts the login form & if valid logs the user in
    if current_user.is_authenticated: #Flask-Login function:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first() # SQLAlchemy function
        if user is None or not user.check_password(form.password.data): # Function in models.py
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data) # Flask-Login function
        next_page = request.args.get('next') # Used to re-direct use back to the page they were trying to access before logging in
        if not next_page or url_parse(next_page).netloc != '': # .netloc security function
            next_page = url_for('index') # If none or index, back to index
        return redirect(next_page) # Otherwise back to the page they were trying to access
    return render_template('login.html', title_page='Sign In', form=form, class_page="form-page chat")

def logout(): # Logout function, logs the user out
    logout_user()
    return redirect(url_for('index'))

def history(): # History function, returns the users chat history (we now call log)
    id = "history"
    messages = current_user.Messages.all() # SQLAlchemy function
    summaries = [] # A list to store the recipe titles
    for message in messages:
        summary = get_summary(message.response)
        summaries.append(summary)
    return render_template('history.html', title_page="History", class_page=id, messages=messages, summaries=summaries)

def get_summary(response): # A function to grab just the recipe's titles for the history page
    start_marker = "Recipe:"
    end_marker = "Ingredients:"
    start_index = response.find(start_marker) + len(start_marker)
    end_index = response.find(end_marker)
    if start_index != -1 and end_index != -1 and start_index < end_index:
        return response[start_index:end_index].strip()
    else:
        return ""

def signup(): # Signup function, accepts the signup form & if valid creates a new user
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('signup.html', title_page="Signup", form=form, class_page="form-page signup")

def chat(): # Chat function, accepts the chat form & if valid sends the user's message to the AI & returns the response
    form = MessageForm()
    id = "chat"
    if form.validate_on_submit():
        user_message = form.content.data
        gpt_response = chat_with_gpt(user_message)
        message = Message(content=user_message, response=gpt_response, author=current_user)
        db.session.add(message)
        db.session.commit()
        flash('Your message has been sent!')
        return redirect(url_for('chat'))
    messages = current_user.Messages.all() 
    return render_template('chat.html', title_page="Chat", class_page="form-page chat", messages=messages, form=form)


def chat_with_gpt(message): # Updated! Switched to gpt-3.5-turbo model as it offers more functionality, passes the context + user message to GPT-3 & returns the response
    response = client.chat.completions.create(model="gpt-3.5-turbo",
    temperature = 0.8,
    max_tokens = 200,
    messages=[
        {"role": "system", "content": "For any (or all) of the food ingredients provided in this message, please suggest a 30-60 minute recipe including the required ingredients and brief instructions on how to cook it. Feel free to add basic pantry ingredients like salt, sugar, flour, etc. Please respond in the format Recipe: [Recipe Name]. Ingredients: [Ingredients]. Cook: [Instructions]. If you detect no ingredients in the given message, please reply 'No ingredients detected, please try again!'"},
        {"role": "user", "content": message}
    ])
    if response.choices:
        return response.choices[0].message.content
    return "Our expert chef's are busy taking other calls at the moment, please check back later"     # Return a default response if ChatGPT doesn't generate any response