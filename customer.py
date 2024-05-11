from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash, jsonify
from flask_hashing import Hashing
from config import get_cursor, allowed_file, MAX_FILENAME_LENGTH
from werkzeug.utils import secure_filename
from zoneinfo import ZoneInfo 
import re
import os
from datetime import date


from auth import role_required
from datetime import datetime,date,timedelta

customer_blueprint = Blueprint('customer', __name__)
hashing = Hashing()

# Get customer information + account information
def get_customer_info(email):
    connection, cursor = get_cursor()
    cursor.execute("""
        SELECT customer.*
        FROM account 
        JOIN customer ON account.account_id = customer.account_id
        WHERE account.email = %s
    """, (email,))
    customer_info = cursor.fetchone()
    cursor.close()
    connection.close()
    return customer_info

# # Get unread messages
def get_unread_messages(customer_id):
    connection, cursor = get_cursor()
    cursor.execute("""
        SELECT message.*,
               CASE
                   WHEN customer_id IS NOT NULL THEN 'customer'
                   WHEN staff_id IS NOT NULL THEN 'staff'
               END AS sender_type
        FROM message
        WHERE message.customer_id = %s AND message.is_read = FALSE
    """, (customer_id,))
    unread_messages = cursor.fetchall()
    cursor.close()
    connection.close()
    return unread_messages

# Dashboard
@customer_blueprint.route('/')
@role_required(['customer'])
def customer():
    email = session.get('email')
    customer_info = get_customer_info(email)
    unread_messages = get_unread_messages(customer_info['customer_id'])
    return render_template('customer/customer_dashboard.html', customer_info=customer_info, unread_messages=unread_messages)



# def get_db_connection():
#     return pymysql.connect(host=dbhost, user=dbuser, password=dbpass, 
#                            database=dbname, cursorclass=pymysql.cursors.DictCursor)

# @customer_blueprint.route('/booking')
# @role_required(['customer'])
# def booking_room():
#     # Render the booking room page
#     return render_template('customer/booking_room.html')

# @customer_blueprint.route('/search', methods=['POST'])
# def search():
#     start_date = request.form['daterange'].split(' - ')[0]
#     end_date = request.form['daterange'].split(' - ')[1]
#     guests = int(request.form['number_of_guests']) 
#     connection = get_db_connection()
#     results = []

#     try:
#         with connection.cursor() as cursor:
#             sql = """
#             SELECT room_id, room_type, room_description, space, IF(room_type = 'dorm', bed_prize, room_prize) AS price, capacity,
#                    IF(capacity >= %s, 'Available', 'Not Available') AS availability
#             FROM accommodation
#             WHERE capacity >= %s AND room_status = 'Open'
#             """
#             cursor.execute(sql, (guests, guests))
#             results = cursor.fetchall()
#     finally:
#         connection.close()  

#     return jsonify(results) 


#     return jsonify(results)  


# @customer_blueprint.route('/book', methods=['POST'])
# def book_room():
#     room_id = request.form['room_id']
#     start_date = request.form['start_date']
#     end_date = request.form['end_date']
#     guests = request.form['number_of_guests']
#     user_id = session.get('user_id') 
#     connection = get_db_connection()

#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("SELECT room_prize FROM accommodation WHERE room_id = %s", (room_id,))
#             room_price = cursor.fetchone()['room_prize']
#             total_days = (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days + 1
#             total_price = room_price * total_days

#             sql = """
#             INSERT INTO bookings (customer_id, room_id, start_date, end_date, number_of_guests, status, total_price)
#             VALUES (%s, %s, %s, %s, %s, 'booked', %s)
#             """
#             cursor.execute(sql, (user_id, room_id, start_date, end_date, guests, total_price))
#             connection.commit()
#         return jsonify({'success': True, 'totalPrice': total_price}) 
#     except Exception as e:
#         return jsonify({'success': False, 'error': str(e)})  
#     finally:
#         connection.close()


# Define a name for upload image profile
def upload_image_profile(customer_id, file):
    filename = secure_filename(file.filename)
    unique_filename = f"user_{customer_id}_{filename}"

    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(base_dir, 'static/customer/')
    file_path = os.path.join(upload_folder, unique_filename)

    # Check if the file path already exists
    if os.path.exists(file_path):
        os.remove(file_path)

    file.save(file_path)
    connection, cursor = get_cursor()
    cursor.execute("UPDATE customer SET profile_image = %s WHERE customer_id = %s", (unique_filename, customer_id))
    connection.commit()

#Handling image update
@customer_blueprint.route('/upload_image_profile', methods=["POST"])
@role_required(['customer'])
def handle_upload_image_profile():
    if 'profile_image' not in request.files:
        flash('No file part')
        return redirect(url_for('customer.customer_updateprofile'))

    file = request.files['profile_image']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('customer.customer_updateprofile'))

    if len(file.filename) > MAX_FILENAME_LENGTH:
        flash('File name is too long')
        return redirect(url_for('customer.customer_updateprofile'))

    if file and allowed_file(file.filename):
        account_id = session.get('id')
        connection, cursor = get_cursor()
        cursor.execute("SELECT role FROM account WHERE account_id = %s", (account_id,))
        result = cursor.fetchone()
        if result is not None and result['role'] == 'customer':
            cursor.execute("SELECT customer_id FROM customer WHERE account_id = %s", (account_id,))
            result = cursor.fetchone()
            if result is not None:
                upload_image_profile(result['customer_id'], file)
                flash('Profile image successfully uploaded')
        else:
            flash('You do not have permission to perform this action')
        return redirect(url_for('customer.customer_updateprofile'))
    else:
        flash('Invalid file type')
        return redirect(url_for('customer.customer_updateprofile'))

#customer update profile
@customer_blueprint.route('/customer_updateprofile', methods=["GET", "POST"])
@role_required(['customer'])
def customer_updateprofile():
    email = session.get('email')
    account_id = session.get('id')
    customer_info = get_customer_info(email)
    connection, cursor = get_cursor()
    
    # Initially fetch the customer_id and other details
    cursor.execute(
        'SELECT a.email, m.* FROM account a INNER JOIN customer m ON a.account_id = m.account_id WHERE a.account_id = %s', 
        (account_id,))

    account = cursor.fetchone()
    customer_id = account['customer_id'] if account else None

    if request.method == 'POST':
        email = request.form['email']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        phone_number = request.form['phone_number']
        date_of_birth = request.form['date_of_birth']
        gender = request.form['gender'].lower()
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        

        # Update password check
        if new_password and new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return render_template('customer/customer_updateprofile.html', account=account, customer_info=customer_info)

        if new_password and (len(new_password) < 8 or not any(char.isupper() for char in new_password) 
            or not any(char.islower() for char in new_password) or not any(char.isdigit() for char in new_password)):
            flash('Password must be at least 8 characters long and contain a mix of uppercase, lowercase, and numeric characters.', 'error')
            return redirect(url_for('customer.customer_updateprofile'))

        # Update the account table for email and password
        if new_password:
            password_hash = hashing.hash_value(new_password, salt='S1#e2!r3@t4$')
            cursor.execute('UPDATE account SET email = %s, password = %s WHERE account_id = %s', 
                           (email, password_hash, account_id))
        else:
            cursor.execute('UPDATE account SET email = %s WHERE account_id = %s', (email, account_id))
        
        # Commit changes to the database
        connection.commit()

        # Update the customer table using customer_id 
        cursor.execute("""
            UPDATE customer SET first_name = %s, last_name = %s, phone_number = %s, date_of_birth = %s, 
            gender = %s WHERE customer_id = %s
            """, (first_name, last_name, phone_number, date_of_birth, gender, customer_id))

        # Commit changes to the database
        connection.commit()

        flash('Profile updated successfully.')
        return redirect(url_for('customer.customer'))

    # Render page with current account information
    return render_template('customer/customer_updateprofile.html', account=account, customer_info=customer_info)