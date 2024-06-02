from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash, jsonify
from flask_hashing import Hashing
from config import get_cursor, allowed_file, MAX_FILENAME_LENGTH
from werkzeug.utils import secure_filename
from zoneinfo import ZoneInfo 
import re
import os
import decimal 
from decimal import Decimal
import pandas as pd
from datetime import date,timedelta,datetime
import pytz
from auth import role_required

customer_blueprint = Blueprint('customer', __name__)
hashing = Hashing()
nz_tz = pytz.timezone('Pacific/Auckland')

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
def booking_room():
    return render_template('customer/booking_room.html')

@customer_blueprint.route('/search', methods=['POST'])
def search():
    date_range = request.form['daterange'].split(' - ')
    start_date = datetime.strptime(date_range[0], '%d/%m/%Y').strftime('%Y-%m-%d')
    end_date = datetime.strptime(date_range[1], '%d/%m/%Y').strftime('%Y-%m-%d')
    adults = int(request.form['adults'])
    children_0_2 = int(request.form['children_0_2'])
    children2_17 = int(request.form['children_2_17'])
    total_guests = adults + children2_17

    connection, cursor = get_cursor()
    results = []

    try:
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

import decimal

@customer_blueprint.route('/preview_booking', methods=['GET'])
@role_required(['customer'])
def preview_booking():
    room_id = request.args.get('room_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    adults = request.args.get('adults')
    children_0_2 = request.args.get('children_0_2')
    children_2_17 = request.args.get('children_2_17')
    
    connection, cursor = get_cursor()
    room = None
    gst_rate = decimal.Decimal('0.15')  # GST rate of 15%

    try:
        sql = "SELECT * FROM accommodation WHERE accommodation_id = %s"
        cursor.execute(sql, (room_id,))
        room = cursor.fetchone()

        if room:
            accommodation_type = room['type']  # Get accommodation type
            # Calculate price details
            room_price = room['price_per_night']
            gst_price = room_price * gst_rate
            total_price = room_price + gst_price

            return render_template('customer/preview_booking.html', 
                                   room=room, 
                                   accommodation_type=accommodation_type,  
                                   start_date=start_date, 
                                   end_date=end_date, 
                                   adults=adults, 
                                   children0_2=children_0_2, 
                                   children2_17=children_2_17, 
                                   gst_price=gst_price, 
                                   total_price=total_price,
                                   current_year=date.today().year)
        else:
            return "Room not found", 404

    except Exception as e:
        print("Error: ", str(e))
        return "Internal Server Error", 500
    finally:
        cursor.close()
        connection.close()

@customer_blueprint.route('/booking_payment', methods=['POST'])
@role_required(['customer'])
def booking_payment():
    room_id = request.form['room_id']
    start_date = datetime.strptime(request.form['start_date'], '%d/%m/%Y').strftime('%Y-%m-%d')
    end_date = datetime.strptime(request.form['end_date'], '%d/%m/%Y').strftime('%Y-%m-%d')
    adults = request.form['adults']
    children_0_2 = request.form['children_0_2']
    children_2_17 = request.form['children_2_17']
    card_number = request.form['card_number']
    card_holder = request.form['card_holder']
    expiry_m = request.form['expiry_m']
    expiry_y = request.form['expiry_y']
    cvc = request.form['cvc']
    total_guests = int(adults) + int(children_2_17)
    customer_id = session.get('customer_id')
    is_paid = True
    total_price = decimal.Decimal(request.form.get('total_price', 0))

    connection, cursor = get_cursor()

    try:
        # Insert booking first
        sql_booking = """
        INSERT INTO booking (customer_id, accommodation_id, start_date, end_date, adults, children, is_paid, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql_booking, (customer_id, room_id, start_date, end_date, adults, int(children_0_2) + int(children_2_17), is_paid, 'confirmed'))
        booking_id = cursor.lastrowid

        # Insert payment and get payment_id
        sql_payment = """
        INSERT INTO payment (customer_id, booking_id, payment_type_id, paid_amount)
        VALUES (%s, %s, %s, %s)
        """
        cursor.execute(sql_payment, (customer_id, booking_id, 2, total_price))
        connection.commit()

        flash('Booking Successful and Payment Confirmed', 'success')
        return redirect(url_for('customer.customer'))

    except Exception as e:
        print("Error: ", str(e))
        connection.rollback()
        flash('An error occurred while processing your booking. Please try again.', 'danger')
        return redirect(url_for('customer.preview_booking', room_id=room_id, start_date=request.form['start_date'], end_date=request.form['end_date'], adults=adults, children_0_2=children_0_2, children_2_17=children_2_17))

    finally:
        cursor.close()
        connection.close()


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

    # Fetch the confirmed bookings
    connection, cursor = get_cursor()
    cursor.execute(
            'SELECT b.*, a.type, a.description, a.image, a.price_per_night FROM booking b INNER JOIN accommodation a ON b.accommodation_id = a.accommodation_id WHERE b.customer_id = %s AND b.status = "confirmed"', 
            (customer_id,))
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
    customer_id= booking['customer_id']
    nights = (end_date - start_date).days
    refund_amount = calculate_refund_amount(price_per_night, nights, start_date, paid_amount)
    
    # insert negative payment entry only if there's a refund
    if refund_amount > 0:
        if payment_type_name == 'gift_card':
            cursor = connection.cursor()
            cursor.execute('UPDATE gift_card SET balance = balance + %s WHERE gift_card_id = %s', 
                           (refund_amount, booking['payment_id']))
            cursor.close()
        elif payment_type_name == 'bank_card':
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO payment (customer_id, booking_id, payment_type_id, paid_amount)
                VALUES (%s, %s, %s, %s)
            ''', (customer_id, booking_id, payment_type_id, -refund_amount))
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

    payment_type_name = payment_type_name.replace('_', ' ').title()

    if refund_amount > 0:
        flash(f'Booking cancelled and ${refund_amount} refunded to your {payment_type_name}.', 'success')
    else:
        flash(f'Booking cancelled but no refund as per the cancellation policy.', 'info')
    return redirect(url_for('customer.customer_managebookings'))

def calculate_refund_amount(price_per_night, nights, start_date, paid_amount):
    today = datetime.now().date()
    days_to_start = (start_date - today).days

    # Refund policy
    if days_to_start >= 1:
        return paid_amount  # Full refund
    else:
        return 0 #no refund

# View All Bookings
@customer_blueprint.route('/customer_viewallbookings', methods=["GET"])
@role_required(['customer'])
def customer_viewallbookings():
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

    # Fetch all bookings including the total paid amount for each booking
    connection, cursor = get_cursor()
    cursor.execute(
        '''
        SELECT b.*, a.type, a.description, a.image, a.price_per_night, 
               (SELECT SUM(p.paid_amount) FROM payment p WHERE p.booking_id = b.booking_id) AS total_paid 
        FROM booking b 
        INNER JOIN accommodation a ON b.accommodation_id = a.accommodation_id 
        WHERE b.customer_id = %s
        ''', 
        (customer_id,))
    all_bookings = cursor.fetchall()
    # Update booking statuses if checkout date has passed
    current_date = datetime.now().date()
    for booking in all_bookings:
        end_date = booking['end_date']
        if booking['status'] == 'confirmed' and end_date < current_date:
            booking['status'] = 'confirmed/no-show'

    cursor.close()
    connection.close()

    if not all_bookings:
        flash('No bookings found.', 'info')

    return render_template('customer/customer_viewallbookings.html', all_bookings=all_bookings, customer_info=customer_info)

# Product to cart
def get_products(category_id=None):
    query = """
    SELECT p.product_id, p.name, p.description, p.unit_price, 
           COALESCE(SUM(i.quantity), -1) as quantity, p.image
    FROM product p
    LEFT JOIN inventory i ON p.product_id = i.product_id
    WHERE 1=1
    """
    params = []
    if category_id:
        query += " AND p.category_id = %s"
        params.append(category_id)
    query += " GROUP BY p.product_id"
    
    connection, cursor = get_cursor()
    cursor.execute(query, params)
    products = cursor.fetchall()
    cursor.close()
    connection.close()
    
    for product in products:
        product['out_of_stock'] = (product['quantity'] == 0)
        product['infinite_stock'] = (product['quantity'] == -1)  
    return products

def get_categories():
    connection, cursor = get_cursor()
    cursor.execute("SELECT * FROM product_category")
    categories = cursor.fetchall()
    cursor.close()
    connection.close()
    return categories
def get_product_options():
    connection, cursor = get_cursor()
    query = """
    SELECT po.product_id, po.option_id, po.option_type, po.option_name, po.additional_cost
    FROM product_option po
    """
    cursor.execute(query)
    options = cursor.fetchall()
    cursor.close()
    connection.close()
    product_options = {}
    for option in options:
        product_id = option['product_id']
        if product_id not in product_options:
            product_options[product_id] = {}
        option_type = option['option_type']
        if option_type not in product_options[product_id]:
            product_options[product_id][option_type] = []
        product_options[product_id][option_type].append(option)
        
    for product in get_products():
        if product['product_id'] not in product_options:
            product_options[product['product_id']] = {}
    return product_options

def add_to_cart(customer_id, product_id, quantity, options):
    connection, cursor = get_cursor()
    try:
        query = """
            SELECT ci.cart_item_id 
            FROM cart_item ci
            LEFT JOIN cart_item_option cio ON ci.cart_item_id = cio.cart_item_id
            WHERE ci.customer_id = %s AND ci.product_id = %s
        """
        params = [customer_id, product_id]
        for option_id in options:
            query += " AND EXISTS (SELECT 1 FROM cart_item_option WHERE cart_item_id = ci.cart_item_id AND option_id = %s)"
            params.append(option_id)
        cursor.execute(query, params)
        cart_item = cursor.fetchone()
        if cart_item:
            cart_item_id = cart_item['cart_item_id']
            cursor.execute("UPDATE cart_item SET quantity = quantity + %s WHERE cart_item_id = %s", (quantity, cart_item_id))
        else:
            cursor.execute("INSERT INTO cart_item (customer_id, product_id, quantity) VALUES (%s, %s, %s)", (customer_id, product_id, quantity))
            cart_item_id = cursor.lastrowid
            for option_id in options:
                cursor.execute("INSERT INTO cart_item_option (cart_item_id, option_id) VALUES (%s, %s)", (cart_item_id, option_id))
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        print(f"Error: {e}")
        return False
    finally:
        cursor.close()
        connection.close()


@customer_blueprint.route('/product')
@role_required(['customer'])
def product():
    email = session.get('email')
    customer_info = get_customer_info(email)
    categories = get_categories()
    category_id = request.args.get('category_id')
    products = get_products(category_id=category_id)
    product_options = get_product_options()
    
    return render_template('customer/customer_product.html', customer_info=customer_info, products=products, categories=categories, product_options=product_options)

@customer_blueprint.route('/add_cart', methods=['POST'])
@role_required(['customer'])
def add_cart():
    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 1))
    options = []
    for key in request.form:
        if key.startswith('option_id_') and request.form.get(key):
            options.append(int(request.form.get(key)))
    
    email = session.get('email')
    customer_info = get_customer_info(email)
    
    if add_to_cart(customer_info['customer_id'], product_id, quantity, options):
        flash('Product added to cart successfully', 'success')
    else:
        flash('Failed to add product to cart. Out of stock or insufficient quantity.', 'danger')
    return redirect(url_for('customer.product'))

# Showing Cart
@customer_blueprint.route('/cart', methods=["GET"])
@role_required(['customer'])
def cart():
    email = session.get('email')
    customer_info = get_customer_info(email)
    
    if not customer_info:
        flash("Customer information not found.", "error")
        return redirect(url_for('customer_dashboard'))

    customer_id = customer_info['customer_id']
    connection, cursor = get_cursor()
    cursor.execute("""
        SELECT 
            ci.cart_item_id, 
            ci.quantity, 
            p.product_id, 
            p.name AS product_name, 
            p.unit_price, 
            p.image, 
            GROUP_CONCAT(po.option_name SEPARATOR ', ') AS options, 
            GROUP_CONCAT(po.additional_cost SEPARATOR ', ') AS option_costs
        FROM cart_item ci
        JOIN product p ON ci.product_id = p.product_id
        LEFT JOIN cart_item_option cio ON ci.cart_item_id = cio.cart_item_id
        LEFT JOIN product_option po ON cio.option_id = po.option_id
        WHERE ci.customer_id = %s
        GROUP BY ci.cart_item_id
    """, (customer_id,))
    cart_items = cursor.fetchall()
    total = Decimal('0.00')
    subtotal = Decimal('0.00')
    for item in cart_items:
        item['unit_price'] = Decimal(item['unit_price'])
        options = item['options'].split(', ') if item['options'] else []
        option_cost = item['option_costs'].split(', ') if item['option_costs'] else []
        option_costs = [Decimal(cost) * item['quantity'] for cost in option_cost]
        item['options_with_costs'] = list(zip(options, option_cost))
        item_total = item['unit_price'] * item['quantity']
        option_total = sum(option_costs)
        item['subtotal'] = (item_total + option_total) * Decimal('0.85')
        item['gst'] = (item_total + option_total) * Decimal('0.15')
        item['total'] = item_total + option_total
        total += item['total']

    if total > Decimal('0.00'):
        subtotal = total * Decimal('0.85')
        gst = total * Decimal('0.15')
    else:
        gst = Decimal('0.00')
        subtotal = Decimal('0.00')

    cursor.close()
    connection.close()
    return render_template('customer/customer_cart.html', cart_items=cart_items, total=total, gst=gst, subtotal=subtotal, customer_info=customer_info)

# Remove from cart
@customer_blueprint.route('/remove_from_cart', methods=["POST"])
@role_required(['customer'])
def remove_from_cart():
    cart_item_id = request.form.get('cart_item_id')
    if not cart_item_id:
        flash('Invalid cart item ID.', 'error')
        return redirect(url_for('customer.cart'))
    connection, cursor = get_cursor()
    try:
        cursor.execute("DELETE FROM cart_item_option WHERE cart_item_id = %s", (cart_item_id,))
        cursor.execute("DELETE FROM cart_item WHERE cart_item_id = %s", (cart_item_id,))
        connection.commit()
        flash('Item removed from cart.', 'success')
    except Exception as e:
        connection.rollback()
        flash(f'Failed to remove item from cart. Error: {str(e)}', 'error')
        print(f"Error: {e}")
    finally:
        cursor.close()
        connection.close()
    return redirect(url_for('customer.cart'))




# Showing checkout page
@customer_blueprint.route('/checkout', methods=['GET'])
@role_required(['customer'])
def customer_checkout():
    email = session.get('email')
    customer_info = get_customer_info(email)
    if not customer_info:
        flash("Please login to proceed to checkout.", "info")
        return redirect(url_for('customer.login'))

    return render_template('customer/customer_checkout.html', customer_info=customer_info, special_requests=special_requests)



# Handling checkout request


@customer_blueprint.route('/checkout', methods=['POST'])
@role_required(['customer'])
def checkout():
    email = session.get('email')
    customer_info = get_customer_info(email)
    if not customer_info:
        flash("Customer information not found.", "error")
        return redirect(url_for('customer.cart'))
    
    customer_id = customer_info['customer_id']
    special_requests = request.form.get('special_requests', '')  # 获取 special_requests 字段
    scheduled_pickup_datetime_str = request.form.get('scheduled_pickup_time', '')  

    try:
        # 将字符串转换为 UTC 时间
        scheduled_pickup_datetime_utc = datetime.fromisoformat(scheduled_pickup_datetime_str.replace('Z', '+00:00'))
        # 转换为新西兰时间
        scheduled_pickup_datetime_nz = scheduled_pickup_datetime_utc.astimezone(nz_tz)
    except ValueError as e:
        flash(f"Invalid scheduled pickup time: {e}", "danger")
        return redirect(url_for('customer.cart'))

    connection, cursor = get_cursor()
    try:
        cursor.execute("""
            INSERT INTO orders (customer_id, total_price, status, created_at, special_requests, scheduled_pickup_time) 
            VALUES (%s, %s, 'ordered', NOW(), %s, %s)
        """, (customer_id, 0, special_requests, scheduled_pickup_datetime_nz))  
        order_id = cursor.lastrowid

        cursor.execute("""
            SELECT ci.cart_item_id, ci.product_id, ci.quantity, p.unit_price, 
                   GROUP_CONCAT(po.option_id) AS option_ids,
                   GROUP_CONCAT(po.option_name, ' (+$', po.additional_cost, ')') AS options
            FROM cart_item ci
            JOIN product p ON ci.product_id = p.product_id
            LEFT JOIN cart_item_option cio ON ci.cart_item_id = cio.cart_item_id
            LEFT JOIN product_option po ON cio.option_id = po.option_id
            WHERE ci.customer_id = %s
            GROUP BY ci.cart_item_id
        """, (customer_id,))
        cart_items = cursor.fetchall()
        
        total_price = Decimal('0.00')
        for item in cart_items:
            product_id = item['product_id']
            quantity = item['quantity']
            unit_price = item['unit_price']
            options = item['options'] if item['options'] else ''
            total_price += unit_price * quantity

            cursor.execute("""
                INSERT INTO order_item (order_id, product_id, quantity, options) 
                VALUES (%s, %s, %s, %s)
            """, (order_id, product_id, quantity, options))
            cursor.execute("""
                INSERT INTO paid_item (customer_id, product_id, quantity, price, order_id) 
                VALUES (%s, %s, %s, %s, %s)
            """, (customer_id, product_id, quantity, unit_price, order_id))
            option_ids = item['option_ids'].split(',') if item['option_ids'] else []
            if option_ids: 
                for option_id in option_ids:
                    cursor.execute("""
                        UPDATE inventory 
                        SET quantity = quantity - %s 
                        WHERE product_id = %s AND option_id = %s AND quantity >= %s
                    """, (quantity, product_id, option_id, quantity))
            else:  
                cursor.execute("""
                    UPDATE inventory 
                    SET quantity = quantity - %s 
                    WHERE product_id = %s AND option_id IS NULL AND quantity >= %s
                """, (quantity, product_id, quantity))
        cursor.execute("""
            UPDATE orders SET total_price = %s WHERE order_id = %s
        """, (total_price, order_id))
        
        cursor.execute("""
            INSERT INTO payment (customer_id, payment_type_id, order_id, paid_amount) 
            VALUES (%s, %s, %s, %s)
        """, (customer_id, 1, order_id, total_price))

        cursor.execute("DELETE FROM cart_item_option WHERE cart_item_id IN (SELECT cart_item_id FROM cart_item WHERE customer_id = %s)", (customer_id,))
        cursor.execute("DELETE FROM cart_item WHERE customer_id = %s", (customer_id,))
        connection.commit()
        flash("Payment successful and order created.", "success")
    except Exception as e:
        connection.rollback()
        flash(f"Failed to process payment. Error: {str(e)}", "danger")
    finally:
        cursor.close()
        connection.close()
    return redirect(url_for('customer.orders'))



## View Customer Orders
@customer_blueprint.route('/orders', methods=['GET'])
@role_required(['customer'])
def orders():
    email = session.get('email')
    customer_info = get_customer_info(email)
    if not customer_info:
        flash("Customer information not found.", "error")
        return redirect(url_for('customer_dashboard'))
    customer_id = customer_info['customer_id']
    connection, cursor = get_cursor()
    try:
        # Get current orders
        cursor.execute("""
            SELECT o.order_id, o.total_price, o.status, o.created_at, o.scheduled_pickup_time
            FROM orders o
            WHERE o.customer_id = %s AND o.status NOT IN ('collected', 'cancelled')
            ORDER BY o.created_at DESC
        """, (customer_id,))
        orders = cursor.fetchall()

        # Get historical orders
        cursor.execute("""
            SELECT o.order_id, o.total_price, o.status, o.created_at, o.scheduled_pickup_time
            FROM orders o
            WHERE o.customer_id = %s AND o.status IN ('collected', 'cancelled')
            ORDER BY o.created_at DESC
        """, (customer_id,))
        history_orders = cursor.fetchall()
    except Exception as e:
        flash(f"Failed to retrieve orders. Error: {str(e)}", "danger")
        orders = []
        history_orders = []
    finally:
        cursor.close()
        connection.close()
    return render_template('customer/customer_orders.html', orders=orders, history_orders=history_orders, customer_info=customer_info)

# View Customer Order Details
@customer_blueprint.route('/order_details/<int:order_id>', methods=['GET'])
@role_required(['customer'])
def order_details(order_id):
    email = session.get('email')
    customer_info = get_customer_info(email)
    if not customer_info:
        flash("Customer information not found.", "error")
        return redirect(url_for('customer.orders'))
    customer_id = customer_info['customer_id']
    connection, cursor = get_cursor()
    cursor.execute("SET NAMES utf8mb4;")
    cursor.execute("SET CHARACTER SET utf8mb4;")
    cursor.execute("SET character_set_connection=utf8mb4;")
    cursor.execute("""
        SELECT * FROM orders WHERE order_id = %s AND customer_id = %s
    """, (order_id, customer_id))
    order = cursor.fetchone()
    if not order:
        flash("Order not found.", "error")
        return redirect(url_for('customer.orders'))
    cursor.execute("""
        SELECT oi.*, p.name AS product_name, p.unit_price
        FROM order_item oi
        JOIN product p ON oi.product_id = p.product_id
        WHERE oi.order_id = %s
    """, (order_id,))
    order_items = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('customer/customer_order_details.html', order=order, order_items=order_items, customer_info=customer_info)

@customer_blueprint.route('/cancel_order/<int:order_id>', methods=['POST'])
@role_required(['customer'])
def cancel_order(order_id):
    email = session.get('email')
    customer_info = get_customer_info(email)
    if not customer_info:
        flash("Customer information not found.", "error")
        return redirect(url_for('customer_dashboard'))
    customer_id = customer_info['customer_id']
    connection, cursor = get_cursor()
    try:
        cursor.execute("""
            SELECT o.status 
            FROM orders o
            WHERE o.customer_id = %s AND o.order_id = %s
        """, (customer_id, order_id))
        order = cursor.fetchone()
        if not order or order['status'] != 'ordered':
            flash("Order cannot be cancelled.", "danger")
            return redirect(url_for('customer.order_details', order_id=order_id))
        cursor.execute("""
            UPDATE orders SET status = 'cancelled'
            WHERE order_id = %s AND customer_id = %s
        """, (order_id, customer_id))
        connection.commit()
        flash("Order cancelled successfully.", "success")
    except Exception as e:
        connection.rollback()
        flash(f"Failed to cancel order. Error: {str(e)}", "danger")
    finally:
        cursor.close()
        connection.close()
    return redirect(url_for('customer.orders'))

