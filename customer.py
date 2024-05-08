from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash, jsonify
from flask_hashing import Hashing
from config import get_cursor, allowed_file,UPLOAD_FOLDER
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

# Get unread messages
def get_unread_messages(customer_id):
    connection, cursor = get_cursor()
    cursor.execute("""
        SELECT message.*,
               CASE
                   WHEN manager_id IS NOT NULL THEN 'manager'
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