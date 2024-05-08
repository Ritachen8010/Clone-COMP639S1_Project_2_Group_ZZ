from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash
from flask_hashing import Hashing
from config import get_cursor, allowed_file, UPLOAD_FOLDER, connection
from functools import wraps
import re
import os
from datetime import datetime,timedelta,date
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash

import requests
# create the auth blueprint for authorization view, such as login, register and logout
auth_blueprint = Blueprint('auth', __name__)
# create an instance of hashing
hashing = Hashing()

# decorate function to check if user is logged in
def login_required(f):
    @wraps(f)
    def wrapper_login_required(*args, **kwargs):
        if 'email' not in session:
            return redirect(url_for('auth.login'))
        else:
            return f(*args, **kwargs)
    return wrapper_login_required

# decorate function to check if user has the required role
def role_required(role):
    def decorator(f):
        @wraps(f)
        def wrapper_role_required(*args, **kwargs):
            if "email" in session:
                if session["role"] not in role:
                    return redirect(url_for('auth.unauthorized'))
                else:
                    return f(*args, **kwargs)
            else:
                return redirect(url_for("auth.login"))
        return wrapper_role_required
    return decorator

@auth_blueprint.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'customer')
        phone = request.form['phone']
        first_name = request.form['first_name']
        last_name = request.form['last_name']

        connection, cursor = get_cursor()
        if cursor is None or connection is None:
            flash('Database connection error.')
            return redirect(url_for('auth.register'))

        try:
            cursor.execute("SELECT email FROM account WHERE email = %s", (email,))
            if cursor.fetchone():
                flash('Account already exists!')
                return redirect(url_for('auth.register'))
            
            hashed_password = generate_password_hash(password)
            cursor.execute("INSERT INTO account (email, password, role) VALUES (%s, %s, %s)",
                           (email, hashed_password, role))
            account_id = cursor.lastrowid
            cursor.execute(
                "INSERT INTO customer (account_id, first_name, last_name, phone_number) VALUES (%s, %s, %s, %s)",
                (account_id, first_name, last_name, phone)
            )
            connection.commit()
            flash('Registration successful. Please login.')
            return redirect(url_for('auth.register'))
        except Exception as e:
            connection.rollback()
            flash(f'Error occurred during registration: {str(e)}')
            return redirect(url_for('auth.register'))
        finally:
            cursor.close()
            connection.close()
    else:
        return render_template('home/register.html')



@auth_blueprint.route('/user')
@login_required
def user():
    if session["role"]=="customer":
        return redirect(url_for('customer.customer'))
    elif session["role"]=="staff":
        return redirect(url_for('staff.staff'))
    elif session["role"]=="manager":
        return redirect(url_for('manager.manager'))


@auth_blueprint.route('/login/', methods=['GET', 'POST'])
def login():
    msg = ''  # Message to display on the login page
    if request.method == 'POST' and 'email' in request.form and 'password' in request.form:
        email = request.form['email']
        user_password = request.form['password']
        
        # Retrieve the account details from the database
        connection, cursor = get_cursor()  # 正确获取 cursor 和 connection
        try:
            cursor.execute('SELECT * FROM account WHERE email = %s', (email,))
            account = cursor.fetchone()
            if account:
                account_id, stored_password, role = account['account_id'], account['password'], account['role']
                if hashing.check_value(stored_password, user_password, salt='S1#e2!r3@t4$'):
                    # Retrieve the status of this account
                    cursor.execute('SELECT status FROM customer WHERE account_id = %s \
                                    UNION SELECT status FROM staff WHERE account_id = %s \
                                    UNION SELECT status FROM manager WHERE account_id = %s',
                                    (account_id, account_id, account_id))
                    status = cursor.fetchone()
                    if status and status['status'] == 'active':
                        # Set session variables and redirect the user to the appropriate dashboard
                        session['loggedin'] = True
                        session['id'] = account_id
                        session['email'] = email
                        session['role'] = role
                        # Redirect to home page
                        return redirect(url_for('auth.user'))
                    else:
                        msg = 'Your account is inactive, please contact the manager for more information.'
                else:
                    msg = 'Invalid password'
            else:
                msg = 'Invalid email'
        except Exception as e:
            print(f"Error during login: {e}")
            msg = "An error occurred during login."
        finally:
            cursor.close()
            connection.close()
    
    return render_template('home/login.html', msg=msg)

@auth_blueprint.route('/logout')
@login_required
def logout():
    # Remove session data, this will log the user out
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('email', None)  # Updated from 'username' to 'email'
    session.pop('role', None)

    return redirect(url_for('auth.login'))

@auth_blueprint.route('/unauthorized')
def unauthorized():
    return render_template('unauthorized.html')