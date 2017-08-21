from app import app, db, lm
from calendar import month_name, monthrange
from datetime import datetime, date, timedelta
from flask import render_template, flash, redirect, session, url_for, request, g
from flask_login import login_user, logout_user, current_user, login_required
from .forms import LoginForm, CreateNewAccountForm, EventForm
from math import ceil
from .models import User, Event

# HELPER FUNCTIONS.
# Calculates how many blank boxes at beginning of month are expected by finding the day of week of the
# last day of the previous month.
#   date -      an arbitrary date in the desired month, expected to be a date object.
#   return -    number of blank days expected.
def CalculateBlankDays(date):
    # Find what day the last of the previous month is.
    last_of_the_month = date - timedelta(days = (date.day))
    last_of_the_month_day = last_of_the_month.weekday()
    
    # The number of blank days at the beginning of the month is the weekday number of the
    # last day of the previous month. It is 0 based, so 1 must be added.
    return last_of_the_month_day + 1
    
# Calculate the month to be displayed based on the given months and the current date.
#   months -    change in month based on current real-world month, can be positive or negative, expected to be an int.
#   current_date - current real-world date, expected to be a date object.
#   return -    a date object in the desired month and year.
def CalculateNewDate(months, current_date):
    month = current_date.month - 1 + months
    historical = (months < 0)
    if not historical:
        year = int(current_date.year + month / 12 )
    else: 
        year = int(ceil(current_date.year + month / 12 ))
        
    month = month % 12 + 1
    day = min(current_date.day, monthrange(year, month)[1])
    return date(year, month, day)

# HANDLER FUNCTIONS.
# Sets the user global variable with the current user.
@app.before_request
def before_request():
    g.user = current_user
    
# Returns the user object for the given id, or None if not found.
@lm.user_loader
def load_user(id):
    if id == 'None':
        return None
    return User.query.get(int(id))
    
# Handles the login page.
@app.route('/login', methods = ['GET', 'POST'])
def login():
    # Skip the login page if already logged in.
    already_logged_in = (g.user is not None and g.user.is_authenticated)
    if already_logged_in:
        return redirect(url_for('home'))
        
    # Attempt to log user in on form submission.
    form = LoginForm()
    if form.validate_on_submit():
        # Verify username is in database.
        user = User.query.filter_by(username = form.username.data).first()
        user_not_found = (user is None)
        if user_not_found:
            flash('Invalid login credentials. Please try again.')
            
        else:
            # Verify password is correct for given username.
            # If so, log user in.
            correct_password = (user.password == form.password.data)
            if correct_password:
                user.authenticated = True
                db.session.add(user)
                db.session.commit()
                should_remember_user = form.remember_me.data
                login_user(user, remember = should_remember_user)
                session['remember_me'] = should_remember_user
                return redirect(url_for('home'))
            else:
                flash('Invalid login credentials. Please try again.')
                
    return render_template('login.html', title = 'Sign In', form = form)
                           
# Handles logging out the current user.
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))
          
# Handles the create new account page.        
@app.route('/CreateNewAccount', methods = ['GET', 'POST'])
def CreateNewAccount():
    # Attempt to create new user on form submission.
    form = CreateNewAccountForm()
    if form.validate_on_submit():
        # Verify username doesn't already exist.
        user = User.query.filter_by(username = form.username.data).first()
        user_already_exists = (user is not None)
        if user_already_exists:
            flash('Username already in use, please choose a new one.')
        else:
            # Create new user, add it to database, and log them in.
            username = form.username.data
            password = form.password.data
            user = User(username = username, password = password)
            user.authenticated = True
            db.session.add(user)
            db.session.commit()
            login_user(user, remember = False)
            return redirect(url_for('home'))
    return render_template('CreateNewAccount.html', title = 'Create New Account', form = form)
              
# Handles all month calendar views.              
@app.route('/home/', defaults = {'path': '0'})
@app.route('/home/<path:path>')
@login_required
def home(path):
    # Calculate displayed month.
    # Current month is considered 0, historical months are negative and the future is positive.
    date = datetime.today()
    month = int(path)
    displayed_date = CalculateNewDate(month, date)
    
    # Get month's full name.
    month = displayed_date.month
    month_long_name = month_name[month]
    
    # Calculate number of days in given month.
    # Monthrange returns a tuple of year, number of days, so second value is wanted.
    year = displayed_date.year
    days_in_month = monthrange(year, month)[1]
    
    # Return the appropriate page
    user = g.user
    list_of_events = Event.query.all()
    return render_template('home.html',
        title = month_long_name + ' ' + str(year),
        user = user,
        days_in_month = days_in_month,
        displayed_month = int(path),
        displayed_date = displayed_date,
        list_of_events = list_of_events,
        blank_days_at_start = CalculateBlankDays(displayed_date))
    
# Handles the create event page.
@app.route('/event/', defaults = {'path': ''}, methods = ['GET', 'POST'])
@app.route('/event/<path:month>/<path:day>/<path:year>', methods = ['GET', 'POST'])
@login_required
def event(month, day, year):    
    # Set the date field to the chosen date.
    form = EventForm()
    form.date.data = str(month + '/' + day + '/' + year)
    
    # Create event on submission.
    if form.validate_on_submit():
        user = g.user
        event = Event(
            user = user.id,
            title = form.title.data,
            date = form.date.data,
            time = form.time.data,
            description = form.description.data)
        db.session.add(event)
        db.session.commit()
        return redirect(url_for('home'))
    
    # Return the appropriate page
    user = g.user
    return render_template('event.html',
        title = 'Create New Event',
        user = user,
        form = form,
        view_only = False)
        
# Handle the view event page.
@app.route('/event/<path:id>', methods = ['GET', 'POST'])
@login_required
def ViewEvent(id):    
    # Set the fields to the given event's values.
    Event_Form = EventForm()
    event = Event.query.filter_by(id = id).first()
    Event_Form.title.data = event.title
    Event_Form.date.data = event.date
    Event_Form.time.data = event.time
    Event_Form.description.data = event.description
    
    # Share event with given user on submission.
    if Event_Form.validate_on_submit():
        user = g.user
        recipient = Event_Form.recipient.data
        
        # Verify given username already exists.
        user = User.query.filter_by(username = recipient).first()
        user_already_exists = (user is not None)
        if not user_already_exists:
            flash("Username isn't already in use, please choose a new one.")
        else:
            # Create event for recipient.
            event = Event(
                user = user.id,
                title = Event_Form.title.data ,
                date = Event_Form.date.data,
                time = Event_Form.time.data,
                description = Event_Form.description.data)
            db.session.add(event)
            db.session.commit()
            return redirect(url_for('home'))
    
    # Return the appropriate page
    user = g.user
    return render_template('event.html',
        title = 'Create New Event',
        user = user,
        form = Event_Form,
        view_only = True)
