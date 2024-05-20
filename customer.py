from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash, jsonify
from flask_hashing import Hashing
from config import get_cursor, allowed_file, MAX_FILENAME_LENGTH
from werkzeug.utils import secure_filename
from zoneinfo import ZoneInfo 
import re
import os
import pandas as pd
from datetime import date,timedelta,datetime
from auth import role_required

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

@customer_blueprint.route('/booking')
@role_required(['customer'])
def booking_room():
    # Render the booking room page
    return render_template('customer/booking_room.html')

@customer_blueprint.route('/search', methods=['POST'])
def search():
    date_range = request.form['daterange'].split(' - ')
    start_date = datetime.strptime(date_range[0], '%d/%m/%Y').strftime('%Y-%m-%d')
    end_date = datetime.strptime(date_range[1], '%d/%m/%Y').strftime('%Y-%m-%d')
    adults = int(request.form['adults'])
    children = int(request.form['children'])
    total_guests = adults + children

    connection, cursor = get_cursor()
    results = []

    try:
        # Fetch basic room data and any bookings overlapping the requested dates
        sql = """
        SELECT a.accommodation_id, a.type, a.description, a.capacity, a.price_per_night, a.space,
               EXISTS (
                    SELECT 1 FROM booking b WHERE b.accommodation_id = a.accommodation_id
                    AND b.start_date < %s AND b.end_date > %s
                ) AS is_booked
        FROM accommodation a
        WHERE a.room_status = 'Open'
        """
        cursor.execute(sql, (end_date, start_date))
        rooms = cursor.fetchall()

        for room in rooms:
            if total_guests > room['capacity']:
                room['availability'] = 'Guest number exceeds capacity'
            elif room['type'] in ['Twin', 'Queen']:
                room['availability'] = 'Fully Booked' if room['is_booked'] else '1 Room Left'
            elif room['type'] == 'Dorm':
                cursor.execute("""
                    SELECT SUM(adults + children) AS total_booked
                    FROM booking
                    WHERE accommodation_id = %s
                    AND start_date <= %s AND end_date >= %s
                """, (room['accommodation_id'], start_date, end_date))
                total_booked = cursor.fetchone()['total_booked'] or 0
                remaining_beds = 4 - total_booked  # Dorm has 4 beds

                if remaining_beds <= 0:
                    room['availability'] = 'Fully Booked'
                else:
                    room['availability'] = f"{remaining_beds} Bunks Left"
            
            results.append(room)

    except Exception as e:
        print("Error: ", str(e))
        return jsonify({'success': False, 'error': str(e)})
    finally:
        cursor.close()
        connection.close()

    return jsonify(results)


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

    # Payment type name display fixed
    payment_type_name = payment_type_name.replace('_', ' ').title()

    flash(f'Booking cancelled and ${refund_amount} refunded to your {payment_type_name}.', 'success')
    return redirect(url_for('customer.customer_managebookings'))

def calculate_refund_amount(price_per_night, nights, start_date, paid_amount):
    today = datetime.now().date()
    days_to_start = (start_date - today).days

    # Refund policy
    if days_to_start >= 2:
        return paid_amount  # Full refund
    else:
        return paid_amount * 0.5  # 50% refund
