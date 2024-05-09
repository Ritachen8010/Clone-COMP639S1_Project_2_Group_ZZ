from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash, jsonify
from flask_hashing import Hashing
from config import get_cursor, allowed_file, MAX_FILENAME_LENGTH
from auth import role_required
import re
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename


# create manager blueprint view
manager_blueprint = Blueprint('manager', __name__)
#create an instance of hashing
hashing = Hashing()

# Get manager information + account information
def get_manager_info(email):
    connection, cursor = get_cursor()
    cursor.execute("""
        SELECT manager.*
        FROM account 
        JOIN manager ON account.account_id = manager.account_id
        WHERE account.email = %s
    """, (email,))
    manager_info = cursor.fetchone()
    cursor.close()
    connection.close()
    return manager_info

# Dashboard
@manager_blueprint.route('/')
@role_required(['manager'])
def manager():
    email = session.get('email')
    manager_info = get_manager_info(email)
    return render_template('manager/manager_dashboard.html', manager_info=manager_info) 


# Define a name for upload image profile
def upload_image_profile(manager_id, file):
    filename = secure_filename(file.filename)
    unique_filename = f"user_{manager_id}_{filename}"

    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(base_dir, 'static/manager/')
    file_path = os.path.join(upload_folder, unique_filename)

    # Check if the file path already exists
    if os.path.exists(file_path):
        os.remove(file_path)

    file.save(file_path)
    connection, cursor = get_cursor()
    cursor.execute("UPDATE manager SET profile_image = %s WHERE manager_id = %s", (unique_filename, manager_id))
    connection.commit()

#Handling image update
@manager_blueprint.route('/upload_image_profile', methods=["POST"])
@role_required(['manager'])
def handle_upload_image_profile():
    if 'profile_image' not in request.files:
        flash('No file part')
        return redirect(url_for('manager.manager_updateprofile'))

    file = request.files['profile_image']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('manager.manager_updateprofile'))

    if len(file.filename) > MAX_FILENAME_LENGTH:
        flash('File name is too long')
        return redirect(url_for('manager.manager_updateprofile'))

    if file and allowed_file(file.filename):
        account_id = session.get('id')
        connection, cursor = get_cursor()
        cursor.execute("SELECT role FROM account WHERE account_id = %s", (account_id,))
        result = cursor.fetchone()
        if result is not None and result['role'] == 'manager':
            cursor.execute("SELECT manager_id FROM manager WHERE account_id = %s", (account_id,))
            result = cursor.fetchone()
            if result is not None:
                upload_image_profile(result['manager_id'], file)
                flash('Profile image successfully uploaded')
        else:
            flash('You do not have permission to perform this action')
        return redirect(url_for('manager.manager_updateprofile'))
    else:
        flash('Invalid file type')
        return redirect(url_for('manager.manager_updateprofile'))

#manager update profile
@manager_blueprint.route('/manager_updateprofile', methods=["GET", "POST"])
@role_required(['manager'])
def manager_updateprofile():
    email = session.get('email')
    account_id = session.get('id')
    manager_info = get_manager_info(email)
    connection, cursor = get_cursor()
    
    # Initially fetch the manager_id and other details
    cursor.execute(
        'SELECT a.email, m.* FROM account a INNER JOIN manager m ON a.account_id = m.account_id WHERE a.account_id = %s', 
        (account_id,))

    account = cursor.fetchone()
    manager_id = account['manager_id'] if account else None

    if request.method == 'POST':
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender'].lower()
        position = request.form['position']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        

        # Update password check
        if new_password and new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('manager/manager_updateprofile.html', account=account, manager_info=manager_info)

        if new_password and (len(new_password) < 8 or not any(char.isupper() for char in new_password) 
            or not any(char.islower() for char in new_password) or not any(char.isdigit() for char in new_password)):
            flash('Password must be at least 8 characters long and contain a mix of uppercase, lowercase, and numeric characters.', 'error')
            return redirect(url_for('manager.manager_updateprofile'))

        # Update the account table for email and password
        if new_password:
            password_hash = hashing.hash_value(new_password, salt='S1#e2!r3@t4$')
            cursor.execute('UPDATE account SET email = %s, password = %s WHERE account_id = %s', 
                           (email, password_hash, account_id))
        else:
            cursor.execute('UPDATE account SET email = %s WHERE account_id = %s', (email, account_id))
        
        # Commit changes to the database
        connection.commit()

        # Update the manager table using manager_id 
        cursor.execute("""
            UPDATE manager SET first_name = %s, last_name = %s, phone_number = %s, date_of_birth = %s, 
            gender = %s, position = %s WHERE manager_id = %s
            """, (first_name, last_name, phone_number, date_of_birth, gender, position, manager_id))

        # Commit changes to the database
        connection.commit()

        flash('Profile updated successfully.')
        return redirect(url_for('manager.manager_updateprofile'))

    # Render page with current account information
    return render_template('manager/manager_updateprofile.html', account=account, manager_info=manager_info)