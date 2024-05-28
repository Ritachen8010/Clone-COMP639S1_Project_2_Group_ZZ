from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash, jsonify
from flask_hashing import Hashing
from config import get_cursor, allowed_file, MAX_FILENAME_LENGTH
from auth import role_required
import re
import os
from datetime import date, timedelta
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

    # Set the validation for birthday ages from 16-100
    today = date.today()
    max_date = today - timedelta(days=16*365)
    min_date = today - timedelta(days=100*365)
    max_date_str = (date.today() - timedelta(days=16*365)).strftime("%Y-%m-%d")
    min_date_str = (date.today() - timedelta(days=100*365)).strftime("%Y-%m-%d")

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

        #set the validation for birthday ages from 16-100
        if date_of_birth < min_date_str or date_of_birth > max_date_str:
            flash('Date of birth must be between 16 and 100 years ago.', 'error')
            return render_template('manager/manager_updateprofile.html', account=account, manager_info=manager_info, max_date=max_date_str, min_date=min_date_str)


        # Update the manager table using manager_id 
        cursor.execute("""
            UPDATE manager SET first_name = %s, last_name = %s, phone_number = %s, date_of_birth = %s, 
            gender = %s, position = %s WHERE manager_id = %s
            """, (first_name, last_name, phone_number, date_of_birth, gender, position, manager_id))

        # Commit changes to the database
        connection.commit()

        flash('Profile updated successfully.')
        return redirect(url_for('manager.manager'))

    # Render page with current account information
    return render_template('manager/manager_updateprofile.html', account=account, manager_info=manager_info, max_date=max_date_str, min_date=min_date_str)

# Manager monitor inventory
@manager_blueprint.route('/monitor_inventory')
@role_required(['manager'])
def monitor_inventory():
    category = request.args.get('category')
    page = request.args.get('page', 1, type=int)
    items_per_page = 10
    offset = (page - 1) * items_per_page
    email = session.get('email')
    manager_info = get_manager_info(email)
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

    return render_template('manager/manager_inventory.html', manager_info=manager_info, 
                           inventory=inventory, page=page, items_per_page=items_per_page,
                           categories=categories, category=category)

# Manager update inventory
@manager_blueprint.route('/update_inventory', methods=['POST'])
@role_required(['manager'])
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
        return redirect(url_for('manager.monitor_inventory', page=page, category=category)) 

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
        return redirect(url_for('manager.monitor_inventory', page=page, category=category))

    current_quantity = current_quantity['quantity']
    if current_quantity + new_quantity < 0:
        flash('Invalid quantity. The new quantity cannot make the inventory negative.', 'error')
        return redirect(url_for('manager.monitor_inventory', page=page, category=category))

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

    return redirect(url_for('manager.monitor_inventory', page=page, category=category))

# Define a name for upload product image
def upload_product_image(product_id, file):
    filename = secure_filename(file.filename)
    unique_filename = f"product_{product_id}_{filename}"

    base_dir = os.path.dirname(os.path.abspath(__file__))
    upload_folder = os.path.join(base_dir, 'static/product/')
    file_path = os.path.join(upload_folder, unique_filename)

    file.save(file_path)
    connection, cursor = get_cursor()
    cursor.execute("UPDATE product SET image = %s WHERE product_id = %s", (unique_filename, product_id))
    connection.commit()
    cursor.close()
    connection.close()
    
# Handling product image update
@manager_blueprint.route('/upload_product_image', methods=["POST"])
@role_required(['manager'])
def handle_upload_product_image():
    if 'image' not in request.files:
        flash('No file part')
        return redirect(url_for('manager.monitor_inventory'))

    file = request.files['image']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('manager.monitor_inventory'))

    if len(file.filename) > MAX_FILENAME_LENGTH:
        flash('File name is too long')
        return redirect(url_for('manager.monitor_inventory'))

    if file and allowed_file(file.filename):
        product_id = request.form.get('product_id')
        upload_product_image(product_id, file)
        flash('Product image successfully uploaded')
        return redirect(url_for('manager.monitor_inventory'))
    else:
        flash('Invalid file type')
        return redirect(url_for('manager.monitor_inventory'))
    
# Manager add inventory
@manager_blueprint.route('/add_inventory', methods=['POST'])
@role_required(['manager'])
def add_inventory():
    category_id = request.form.get('category_id')
    option_id = request.form.get('option_id')
    if option_id == 'null':
        option_id = None
    name = request.form.get('name')
    description = request.form.get('description')
    unit_price = request.form.get('unit_price')
    quantity = request.form.get('quantity')
    connection, cursor = get_cursor()


    is_available = True
    cursor.execute("INSERT INTO product (category_id, name, description, unit_price, is_available) VALUES (%s, %s, %s, %s, %s)", (category_id, name, description, unit_price, is_available))

    product_id = cursor.lastrowid

    cursor.execute("SELECT * FROM product WHERE name = %s", (name,))
    existing_product = cursor.fetchone()

    if existing_product is not None:
        flash('A product with the same name already exists')
        connection.rollback()
        return redirect(url_for('manager.monitor_inventory'))

    image = request.files.get('image')
    if image:
        upload_product_image(product_id, image)


    cursor.execute("SELECT * FROM product_option WHERE product_id = %s AND option_id = %s", (product_id, option_id))
    existing_option = cursor.fetchone()

    if existing_option is not None:
        flash('A product with the same name and option already exists')
        connection.rollback()
        return redirect(url_for('manager.monitor_inventory'))
    
    if product_id is not None and option_id is not None:
        cursor.execute("INSERT INTO product_option (product_id, option_type, option_name, additional_cost) VALUES (%s, %s, %s, %s)", (product_id, request.form.get('option_type'), request.form.get('option_name'), request.form.get('additional_cost')))
    
    if product_id is not None:
        if option_id is not None:
            cursor.execute("INSERT INTO inventory (product_id, option_id, quantity) VALUES (%s, %s, %s)", (product_id, option_id, quantity))
        else:
            cursor.execute("INSERT INTO inventory (product_id, quantity) VALUES (%s, %s)", (product_id, quantity))
    
    connection.commit()
    cursor.close()
    connection.close()
    
    flash('Product successfully added to inventory')
    return redirect(url_for('manager.monitor_inventory'))


# Manager edit inventory
# @manager_blueprint.route('/edit_inventory/<int:product_id>', methods=['POST'])
# @role_required(['manager'])
# def edit_inventory(product_id):
#     quantity = request.form.get('quantity')
    # Update the inventory item in the database

# Manager delete inventory
# @manager_blueprint.route('/delete_inventory/<int:product_id>', methods=['POST'])
# @role_required(['manager'])
# def delete_inventory(product_id):
    # Delete the inventory item from the database


    
# Get customer information
def get_customer_info(email):
    connection, cursor = get_cursor()
    cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
    customer = cursor.fetchone()
    cursor.close()
    connection.close()
    return customer
@manager_blueprint.route('/manage_orders', methods=['GET', 'POST'])
@role_required(['manager'])
def manage_orders():
    email = session.get('email')
    manager_info = get_manager_info(email)
    filter_status = request.args.get('status', 'active')
    search_email = request.args.get('search_email', '').strip()
    pickup_date = request.args.get('pickup_date', '').strip()
    
    connection, cursor = get_cursor()

    query = """
        SELECT o.order_id, o.customer_id, o.total_price, o.special_requests, 
               o.scheduled_pickup_time, o.status, o.created_at, o.last_updated,
               c.first_name, c.last_name, acc.email
        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        JOIN account acc ON c.account_id = acc.account_id
        WHERE 1=1
    """
    params = []

    if filter_status != 'active':
        query += " AND o.status = %s"
        params.append(filter_status)
    else:
        query += " AND o.status IN ('ordered', 'preparing', 'ready for collection')"

    if search_email:
        query += " AND acc.email LIKE %s"
        params.append(f"%{search_email}%")

    if pickup_date:
        query += " AND DATE(o.scheduled_pickup_time) = %s"
        params.append(pickup_date)

    query += " ORDER BY o.created_at DESC"

    cursor.execute(query, params)
    orders = cursor.fetchall()

    if request.method == 'POST':
        order_id = request.form.get('order_id')
        new_status = request.form.get('new_status')
        valid_statuses = ['ordered', 'preparing', 'ready for collection', 'collected', 'cancelled']
        if order_id and new_status in valid_statuses:
            cursor.execute("""
                UPDATE orders 
                SET status = %s, last_updated = NOW()
                WHERE order_id = %s
            """, (new_status, order_id))
            connection.commit()
            flash(f"Order {order_id} status updated to {new_status}.", "success")
        else:
            flash(f"Invalid status value: {new_status}", "danger")
        return redirect(url_for('manager.manage_orders', status=filter_status, search_email=search_email, pickup_date=pickup_date))

    cursor.close()
    connection.close()

    return render_template('manager/manager_manage_orders.html', orders=orders, manager_info=manager_info, filter_status=filter_status, search_email=search_email, pickup_date=pickup_date)

#order details
@manager_blueprint.route('/order_details/<int:order_id>', methods=['GET'])
@role_required(['manager'])
def order_details(order_id):
    email = session.get('email')
    manager_info = get_manager_info(email)
    
    connection, cursor = get_cursor()
    cursor.execute("""
        SELECT o.*, c.first_name, c.last_name, acc.email
        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        JOIN account acc ON c.account_id = acc.account_id
        WHERE o.order_id = %s
    """, (order_id,))
    order = cursor.fetchone()
    
    cursor.execute("""
        SELECT oi.*, p.name AS product_name
        FROM order_item oi
        JOIN product p ON oi.product_id = p.product_id
        WHERE oi.order_id = %s
    """, (order_id,))
    order_items = cursor.fetchall()
    
    cursor.close()
    connection.close()
    
    return render_template('manager/manager_order_details.html', order=order, order_items=order_items)


# Manager view history orders
@manager_blueprint.route('/history_orders', methods=['GET', 'POST'])
@role_required(['manager'])
def history_orders():
    email = session.get('email')
    manager_info = get_manager_info(email)
    if not manager_info:
        flash("Manager information not found.", "error")
        return redirect(url_for('manager_dashboard'))

    filter_status = request.args.get('status', '').strip()
    search_email = request.args.get('search_email', '').strip()
    pickup_date = request.args.get('pickup_date', '').strip()
    
    connection, cursor = get_cursor()
    query = """
        SELECT o.order_id, o.customer_id, o.total_price, o.status, o.created_at, o.last_updated,
               o.scheduled_pickup_time, c.first_name, c.last_name, acc.email
        FROM orders o
        JOIN customer c ON o.customer_id = c.customer_id
        JOIN account acc ON c.account_id = acc.account_id
        WHERE o.status IN ('collected', 'cancelled')
    """
    params = []

    if filter_status:
        query += " AND o.status = %s"
        params.append(filter_status)

    if search_email:
        query += " AND acc.email LIKE %s"
        params.append(f"%{search_email}%")

    if pickup_date:
        query += " AND DATE(o.scheduled_pickup_time) = %s"
        params.append(pickup_date)

    query += " ORDER BY o.created_at DESC"

    cursor.execute(query, params)
    history_orders = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('manager/manager_history_orders.html', history_orders=history_orders, manager_info=manager_info, filter_status=filter_status, search_email=search_email, pickup_date=pickup_date)
