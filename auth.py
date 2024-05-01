from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash
from flask_hashing import Hashing
from config import get_cursor, allowed_file, UPLOAD_FOLDER
from functools import wraps
import re
import os
from datetime import datetime,timedelta,date
from werkzeug.utils import secure_filename
import requests
# create the auth blueprint for authorization view, such as login, register and logout
auth_blueprint = Blueprint('auth', __name__)
# create an instance of hashing
hashing = Hashing()

# decorate function to check if user is logged in
def login_required(f):
    @wraps(f)
    def wrapper_login_required(*args,**kwargs):
       if 'username' not in session:
           return redirect(url_for('auth.login'))
       else:
           return f(*args,**kwargs)
    return wrapper_login_required

# decorate function to check if user has the required role
def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper_role_required(*args,**kwargs):  
            if "username" in session:
                if session["role"] not in role:
                    return redirect(url_for('auth.unauthorized'))
                else:
                    return f(*args,**kwargs)
            else:
                return redirect(url_for("auth.login"))
        return wrapper_role_required
    return decorator

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')        


@auth_blueprint.route('/logout')
@login_required
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   session.pop('role', None)

   return redirect(url_for('auth.login'))


@auth_blueprint.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html')

@auth_blueprint.route('/user')
@login_required
def user():
    if session["role"]=="customer":
        return redirect(url_for('customer.customer'))
    elif session["role"]=="staff":
        return redirect(url_for('staff.staff'))
    elif session["role"]=="manager":
        return redirect(url_for('manager.manager'))
    
 # decorate function to check if user is logged in
def login_required(f):
    @wraps(f)
    def wrapper_login_required(*args,**kwargs):
       if 'username' not in session:
           return redirect(url_for('auth.login'))
       else:
           return f(*args,**kwargs)
    return wrapper_login_required
   
# this is the login page
@auth_blueprint.route('/login/', methods=['GET', 'POST'])
def login():
    msg = ''  # Message to display on the login page
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        user_password = request.form['password']
        # Retrieve the account details from the database
        cursor = get_cursor()  
        cursor.execute('SELECT * FROM account WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            account_id, username, stored_password, role = account['account_id'], account['username'], account['password'], account['role']
            if hashing.check_value(stored_password, user_password, salt='S1#e2!r3@t4$'):
                # get the status of this account
                cursor.execute('SELECT status FROM customer WHERE account_id = %s\
                            UNION SELECT status FROM staff WHERE account_id = %s\
                            UNION SELECT status FROM manager WHERE account_id = %s',\
                            (account_id,account_id,account_id))
                status = cursor.fetchone()
                # check if the account status is active
                if status['status'] =='active':
                    # Set session variables and redirect the user to the appropriate dashboard
                    session['loggedin'] = True
                    session['id'] = account_id
                    session['username'] = username
                    session['role'] = role
                    # Redirect to home page
                    return redirect(url_for('auth.user'))
                else:
                    # Output message if the account is inactive.
                    msg = 'Your account is inactive, please contact manager for more infromation.'
            else:
                # Password incorrect
                msg = 'Invalid password'
        else:
            # Account doesnt exist or username incorrect
            msg = 'Invalid username'
    # Render the login page with any message (if applicable)
    return render_template('login.html', msg=msg)





