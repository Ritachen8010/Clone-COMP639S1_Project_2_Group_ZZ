from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash, jsonify
from flask_hashing import Hashing
from config import get_cursor, allowed_file, MAX_FILENAME_LENGTH
import re
import os
from datetime import datetime, timedelta
from auth import role_required
from werkzeug.utils import secure_filename

staff_blueprint = Blueprint('staff', __name__)
hashing = Hashing()
 
# Get staff information + account information
def get_staff_info(email):
    connection, cursor = get_cursor()
    cursor.execute("""
        SELECT staff.*
        FROM account 
        JOIN staff ON account.account_id = staff.account_id
        WHERE account.email = %s
    """, (email,))
    staff_info = cursor.fetchone()
    cursor.close()
    connection.close()
    return staff_info

@staff_blueprint.route('/')
@role_required(['staff'])
def staff():
    email = session.get('email')
    staff_info = get_staff_info(email)
    return render_template('staff/staff_dashboard.html',active='dashboard', staff_info=staff_info) 


# Define a name for upload image profile
def upload_image_profile(staff_id, file):
    filename = secure_filename(file.filename)
    unique_filename = f"user_{staff_id}_{filename}"

    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(base_dir, 'static/staff/')
    file_path = os.path.join(upload_folder, unique_filename)

    # Check if the file path already exists
    if os.path.exists(file_path):
        os.remove(file_path)

    file.save(file_path)
    connection, cursor = get_cursor()
    cursor.execute("UPDATE staff SET profile_image = %s WHERE staff_id = %s", (unique_filename, staff_id))
    connection.commit()


#Handling image update
@staff_blueprint.route('/upload_image_profile', methods=["POST"])
@role_required(['staff'])
def handle_upload_image_profile():
    if 'profile_image' not in request.files:
        flash('No file part')
        return redirect(url_for('staff.staff_updateprofile'))

    file = request.files['profile_image']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('staff.staff_updateprofile'))

    if len(file.filename) > MAX_FILENAME_LENGTH:
        flash('File name is too long')
        return redirect(url_for('staff.staff_updateprofile'))

    if file and allowed_file(file.filename):
        account_id = session.get('id')
        connection, cursor = get_cursor()
        cursor.execute("SELECT role FROM account WHERE account_id = %s", (account_id,))
        result = cursor.fetchone()
        if result is not None and result['role'] == 'staff':
            cursor.execute("SELECT staff_id FROM staff WHERE account_id = %s", (account_id,))
            result = cursor.fetchone()
            if result is not None:
                upload_image_profile(result['staff_id'], file)
                flash('Profile image successfully uploaded')
        else:
            flash('You do not have permission to perform this action')
        return redirect(url_for('staff.staff_updateprofile'))
    else:
        flash('Invalid file type')
        return redirect(url_for('staff.staff_updateprofile'))

#staff update profile
@staff_blueprint.route('/staff_updateprofile', methods=["GET", "POST"])
@role_required(['staff'])
def staff_updateprofile():
    email = session.get('email')
    account_id = session.get('id')
    staff_info = get_staff_info(email)
    connection, cursor = get_cursor()
    
    # Initially fetch the staff_id and other details
    cursor.execute(
        'SELECT a.email, s.* FROM account a INNER JOIN staff s ON a.account_id = s.account_id WHERE a.account_id = %s', 
        (account_id,))

    account = cursor.fetchone()
    staff_id = account['staff_id'] if account else None

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
            return render_template('staff/staff_updateprofile.html', account=account)

        if new_password and (len(new_password) < 8 or not any(char.isupper() for char in new_password) 
            or not any(char.islower() for char in new_password) or not any(char.isdigit() for char in new_password)):
            flash('Password must be at least 8 characters long and contain a mix of uppercase, lowercase, and numeric characters.', 'error')
            return redirect(url_for('staff.staff_updateprofile'))

        # Update the account table for email and password
        if new_password:
            password_hash = hashing.hash_value(new_password, salt='S1#e2!r3@t4$')
            cursor.execute('UPDATE account SET email = %s, password = %s WHERE account_id = %s', 
                           (email, password_hash, account_id))
        else:
            cursor.execute('UPDATE account SET email = %s WHERE account_id = %s', (email, account_id))
        
        # Commit changes to the database
        connection.commit()

        # Update the staff table using staff_id 
        cursor.execute("""
            UPDATE staff SET first_name = %s, last_name = %s, phone_number = %s, date_of_birth = %s, 
            gender = %s, position = %s WHERE staff_id = %s
            """, (first_name, last_name, phone_number, date_of_birth, gender, position, staff_id))

        # Commit changes to the database
        connection.commit()

        flash('Profile updated successfully.')
        return redirect(url_for('staff.staff_updateprofile'))

    # Render page with current account information
    return render_template('staff/staff_updateprofile.html', account=account, staff_info=staff_info)
