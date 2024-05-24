from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash, jsonify
from flask_hashing import Hashing
from config import get_cursor, allowed_file, MAX_FILENAME_LENGTH
import re
import os
from datetime import date, timedelta
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
    
    # Set the validation for birthday ages from 16-100
    today = date.today()
    max_date = today - timedelta(days=16*365)
    min_date = today - timedelta(days=100*365)
    max_date_str = (date.today() - timedelta(days=16*365)).strftime("%Y-%m-%d")
    min_date_str = (date.today() - timedelta(days=100*365)).strftime("%Y-%m-%d")

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
            return render_template('staff/staff_updateprofile.html', account=account, staff_info=staff_info)

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

        #set the validation for birthday ages from 16-100
        if date_of_birth < min_date_str or date_of_birth > max_date_str:
            flash('Date of birth must be between 16 and 100 years ago.', 'error')
            return render_template('staff/staff_updateprofile.html', account=account, staff_info=staff_info, max_date=max_date_str, min_date=min_date_str)


        # Update the staff table using staff_id 
        cursor.execute("""
            UPDATE staff SET first_name = %s, last_name = %s, phone_number = %s, date_of_birth = %s, 
            gender = %s, position = %s WHERE staff_id = %s
            """, (first_name, last_name, phone_number, date_of_birth, gender, position, staff_id))

        # Commit changes to the database
        connection.commit()

        flash('Profile updated successfully.')
        return redirect(url_for('staff.staff'))

    # Render page with current account information
    return render_template('staff/staff_updateprofile.html', account=account, staff_info=staff_info, max_date=max_date_str, min_date=min_date_str)

# Staff view orders
@staff_blueprint.route('/orders', methods=['GET'])
@role_required(['staff'])
def view_orders():
    email = session.get('email')
    staff_info = get_staff_info(email)
    
    connection, cursor = get_cursor()
    
    try:
        cursor.execute("""
            SELECT o.order_id, o.total_price, o.status, o.created_at, 
                   c.first_name, c.last_name
            FROM orders o
            JOIN customer c ON o.customer_id = c.customer_id
            ORDER BY o.created_at DESC
        """)
        orders = cursor.fetchall()
    except Exception as e:
        flash(f"Failed to retrieve orders. Error: {str(e)}", "danger")
        orders = []
    finally:
        cursor.close()
        connection.close()
    
    return render_template('staff/staff_vieworders.html', orders=orders, staff_info=staff_info)

@staff_blueprint.route('/order_details/<int:order_id>', methods=['GET'])
@role_required(['staff'])
def order_details(order_id):
    email = session.get('email')
    staff_info = get_staff_info(email)
    
    connection, cursor = get_cursor()
    
    try:
        cursor.execute("SET NAMES utf8mb4;")
        cursor.execute("SET CHARACTER SET utf8mb4;")
        cursor.execute("SET character_set_connection=utf8mb4;")
        
        cursor.execute("""
            SELECT o.*, c.first_name, c.last_name
            FROM orders o
            JOIN customer c ON o.customer_id = c.customer_id
            WHERE o.order_id = %s
        """, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            flash("Order not found.", "error")
            return redirect(url_for('staff.view_orders'))
        
        cursor.execute("""
            SELECT oi.*, p.name AS product_name, p.unit_price
            FROM order_item oi
            JOIN product p ON oi.product_id = p.product_id
            WHERE oi.order_id = %s
        """, (order_id,))
        order_items = cursor.fetchall()
    except Exception as e:
        flash(f"Failed to retrieve order details. Error: {str(e)}", "danger")
        order = None
        order_items = []
    finally:
        cursor.close()
        connection.close()
    
    return render_template('staff/staff_order_details.html', order=order, order_items=order_items, staff_info=staff_info)
@staff_blueprint.route('/monitor_inventory')
@role_required(['staff'])
def monitor_inventory():
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    items_per_page = 10
    offset = (page - 1) * items_per_page
    email = session.get('email')
    staff_info = get_staff_info(email)
    connection, cursor = get_cursor()

    if category:
        cursor.execute("""
            SELECT
                inventory.product_id,
                inventory.option_id,
                product_category.name AS category,
                CONCAT(product.name, ' ', COALESCE(product_option.option_name, '')) AS name,
                product.description,
                product.unit_price,
                inventory.quantity,
                inventory.last_updated,
                staff.first_name AS staff_first_name,
                staff.last_name AS staff_last_name,
                manager.first_name AS manager_first_name,
                manager.last_name AS manager_last_name
            FROM inventory 
            LEFT JOIN product ON inventory.product_id = product.product_id
            LEFT JOIN staff ON inventory.staff_id = staff.staff_id
            LEFT JOIN manager ON inventory.manager_id = manager.manager_id
            LEFT JOIN product_category ON product.category_id = product_category.category_id
            LEFT JOIN product_option ON inventory.option_id = product_option.option_id
            WHERE product_category.name = %s
            ORDER BY name
            LIMIT %s OFFSET %s
        """, (category, items_per_page, offset))
    else:
        cursor.execute("""
            SELECT
                inventory.product_id,
                inventory.option_id,
                product_category.name AS category,
                CONCAT(product.name, ' ', COALESCE(product_option.option_name, '')) AS name,
                product.description,
                product.unit_price,
                inventory.quantity,
                inventory.last_updated,
                staff.first_name AS staff_first_name,
                staff.last_name AS staff_last_name,
                manager.first_name AS manager_first_name,
                manager.last_name AS manager_last_name
            FROM inventory 
            LEFT JOIN product ON inventory.product_id = product.product_id
            LEFT JOIN staff ON inventory.staff_id = staff.staff_id
            LEFT JOIN manager ON inventory.manager_id = manager.manager_id
            LEFT JOIN product_category ON product.category_id = product_category.category_id
            LEFT JOIN product_option ON inventory.option_id = product_option.option_id
            ORDER BY name
            LIMIT %s OFFSET %s
        """, (items_per_page, offset))

    inventory = cursor.fetchall()

    # Query all categories
    cursor.execute("SELECT name FROM product_category")
    categories = cursor.fetchall()
    categories = [row['name'] for row in categories]

    # Remove duplicates by converting the list to a set, then convert it back to a list
    categories = list(set(categories))
    cursor.close()
    connection.close()

    return render_template('staff/staff_inventory.html', staff_info=staff_info, 
                           inventory=inventory, page=page, items_per_page=items_per_page,
                           categories=categories, category=category)

# Staff update inventory
@staff_blueprint.route('/update_inventory', methods=['POST'])
@role_required(['staff'])
def update_inventory():
    product_id = request.form.get('product_id')
    option_id = request.form.get('option_id')
    new_quantity = request.form.get('quantity')
    page = request.form.get('page', 1, type=int)
    category = request.form.get('category')
    connection, cursor = get_cursor()

    # Validate new_quantity
    try:
        new_quantity = int(new_quantity)
        if abs(new_quantity) > 100:
            raise ValueError
    except ValueError:
        flash('Invalid quantity. The maximum inventory limit per entry is 100.', 'error')
        return redirect(url_for('staff.monitor_inventory', page=page, category=category)) 

    # Check if the new quantity will make the inventory negative
    if option_id and option_id.isdigit():
        cursor.execute("""
            SELECT quantity FROM inventory WHERE product_id = %s AND option_id = %s
        """, (product_id, option_id))
    else:
        cursor.execute("""
            SELECT quantity FROM inventory WHERE product_id = %s
        """, (product_id,))

    current_quantity = cursor.fetchone()
    if current_quantity is None:
        flash('Product not found in inventory.', 'error')
        return redirect(url_for('staff.monitor_inventory', page=page, category=category))

    current_quantity = current_quantity['quantity']
    if current_quantity + new_quantity < 0:
        flash('Invalid quantity. The new quantity cannot make the inventory negative.', 'error')
        return redirect(url_for('staff.monitor_inventory', page=page, category=category))

    if option_id and option_id.isdigit():
        cursor.execute("""
            UPDATE inventory
            SET quantity = quantity + %s
            WHERE product_id = %s AND option_id = %s
        """, (new_quantity, product_id, option_id))
    else:
        cursor.execute("""
            UPDATE inventory
            SET quantity = quantity + %s
            WHERE product_id = %s
        """, (new_quantity, product_id))

    connection.commit()
    cursor.close()
    connection.close()

    return redirect(url_for('staff.monitor_inventory', page=page, category=category))
