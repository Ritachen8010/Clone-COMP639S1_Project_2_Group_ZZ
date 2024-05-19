from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash, jsonify
from flask_hashing import Hashing
from config import get_cursor, allowed_file, MAX_FILENAME_LENGTH
from werkzeug.utils import secure_filename
from zoneinfo import ZoneInfo 
import re
import os
from datetime import date,timedelta


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
    
    # Set the validation for birthday ages from 16-100
    today = date.today()
    max_date = today - timedelta(days=16*365)
    min_date = today - timedelta(days=100*365)
    max_date_str = (date.today() - timedelta(days=16*365)).strftime("%Y-%m-%d")
    min_date_str = (date.today() - timedelta(days=100*365)).strftime("%Y-%m-%d")

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

        #set the validation for birthday ages from 16-100
        if date_of_birth < min_date_str or date_of_birth > max_date_str:
            flash('Date of birth must be between 16 and 100 years ago.', 'error')
            return render_template('customer/customer_updateprofile.html', account=account, customer_info=customer_info, max_date=max_date_str, min_date=min_date_str)

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
    return render_template('customer/customer_updateprofile.html', account=account, customer_info=customer_info,max_date=max_date_str, min_date=min_date_str)




#Customer view bookings
@customer_blueprint.route('/customer_viewbookings', methods=["GET"])
@role_required(['customer'])
def customer_viewbookings():
    email = session.get('email')
    account_id = session.get('id')    
    connection, cursor = get_cursor()
    customer_info = get_customer_info(email)

    cursor.execute(
        'SELECT a.email, c.customer_id FROM account a INNER JOIN customer c ON a.account_id = c.account_id WHERE a.account_id = %s', 
        (account_id,))
    account_info = cursor.fetchone()
    cursor.close()
    connection.close()
    if not account_info:
        flash('No customer information found.', 'error')
        return redirect(url_for('customer.customer_dashboard'))

    customer_id = account_info['customer_id']

    
    # Fetch the bookings 
    connection, cursor = get_cursor()
    cursor.execute(
        'SELECT b.*, a.type, a.description, a.image, a.price_per_night FROM booking b INNER JOIN accommodation a ON b.accommodation_id = a.accommodation_id WHERE b.customer_id = %s', 
        (customer_id,))
    bookings = cursor.fetchall()
    cursor.close()
    connection.close()


    if not bookings:
        flash('No bookings found.', 'info')

    return render_template('customer/customer_viewbookings.html', bookings=bookings, customer_info=customer_info)


#manage bookings
@customer_blueprint.route('/customer_managebookings', methods=["GET"])
@role_required(['customer'])
def customer_managebookings():
    email = session.get('email')
    account_id = session.get('id')    
    connection, cursor = get_cursor()
    customer_info = get_customer_info(email)

    cursor.execute(
        'SELECT a.email, c.customer_id FROM account a INNER JOIN customer c ON a.account_id = c.account_id WHERE a.account_id = %s', 
        (account_id,))
    account_info = cursor.fetchone()
    cursor.close()
    connection.close()
    if not account_info:
        flash('No customer information found.', 'error')
        return redirect(url_for('customer.customer_dashboard'))

    customer_id = account_info['customer_id']

    # Fetch the bookings with date filter, excluding cancelled bookings
    connection, cursor = get_cursor()
    today = datetime.now().date()
    cursor.execute(
        'SELECT b.*, a.type, a.description, a.image, a.price_per_night FROM booking b INNER JOIN accommodation a ON b.accommodation_id = a.accommodation_id WHERE b.customer_id = %s AND b.start_date >= %s AND b.status != "cancelled"', 
        (customer_id, today))
    bookings = cursor.fetchall()
    cursor.close()
    connection.close()

    if not bookings:
        flash('No bookings found.', 'info')

    return render_template('customer/customer_managebookings.html', bookings=bookings, customer_info=customer_info)



# cancel booking
@customer_blueprint.route('/cancel_booking', methods=["GET"])
@role_required(['customer'])
def cancel_booking():
    booking_id = request.args.get('booking_id')
    if not booking_id:
        flash('Invalid booking ID.', 'error')
        return redirect(url_for('customer.customer_managebookings'))

    connection, cursor = get_cursor()
    cursor.execute('''
        SELECT b.*, a.price_per_night, p.payment_type_id, p.paid_amount, pt.payment_type 
        FROM booking b 
        JOIN accommodation a ON b.accommodation_id = a.accommodation_id
        JOIN payment p ON b.booking_id = p.booking_id
        JOIN payment_type pt ON p.payment_type_id = pt.payment_type_id
        WHERE b.booking_id = %s
    ''', (booking_id,))
    booking = cursor.fetchall()
    cursor.close()

    if not booking:
        connection.close()
        flash('Booking not found.', 'error')
        return redirect(url_for('customer.customer_managebookings'))

    booking = booking[0]  # Get the first result

    # Calculate refund amount
    payment_type_id = booking['payment_type_id']
    paid_amount = booking['paid_amount']
    payment_type_name = booking['payment_type']
    price_per_night = booking['price_per_night']
    start_date = booking['start_date']
    end_date = booking['end_date']
    nights = (end_date - start_date).days
    refund_amount = calculate_refund_amount(price_per_night, nights, start_date, paid_amount)

    # Use a new cursor to insert negative payment entry
    cursor = connection.cursor()
    cursor.execute('''
        INSERT INTO payment (customer_id, payment_type_id, booking_id, paid_amount)
        VALUES (%s, %s, %s, %s)
    ''', (booking['customer_id'], payment_type_id, booking_id, -refund_amount))
    cursor.close()

    # Update gift card balance if applicable
    if payment_type_id == 1:  # Gift card
        cursor = connection.cursor()
        cursor.execute('UPDATE gift_card SET balance = balance + %s WHERE gift_card_id = %s', 
                       (refund_amount, booking['payment_id']))
        cursor.close()

    # Update the booking status to cancelled
    cursor = connection.cursor()
    cursor.execute('''
        UPDATE booking 
        SET status = 'cancelled' 
        WHERE booking_id = %s
    ''', (booking_id,))
    cursor.close()

    # Remove blocked dates
    cursor = connection.cursor()
    cursor.execute('''
        DELETE FROM blocked_dates 
        WHERE accommodation_id = %s AND start_date = %s AND end_date = %s
    ''', (booking['accommodation_id'], start_date, end_date))
    cursor.close()

    connection.commit()
    connection.close()

    flash(f'Booking cancelled and {refund_amount} refunded to your {payment_type_name}.', 'success')
    return redirect(url_for('customer.customer_managebookings'))

def calculate_refund_amount(price_per_night, nights, start_date, paid_amount):
    today = datetime.now().date()
    days_to_start = (start_date - today).days

    # Refund policy
    if days_to_start >= 2:
        return paid_amount  # Full refund
    else:
        return paid_amount * 0.5  # 50% refund
