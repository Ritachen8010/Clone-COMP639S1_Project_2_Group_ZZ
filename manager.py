from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash, jsonify
from config import get_cursor, allowed_file, MAX_FILENAME_LENGTH
from auth import role_required
import re
import os
from datetime import date, timedelta, datetime
from werkzeug.utils import secure_filename


from extensions import socketio, hashing  
from config import get_cursor, get_customer_info_by_id, get_staff_info_by_id
from flask_socketio import join_room, leave_room, send

# create manager blueprint view
manager_blueprint = Blueprint('manager', __name__)
#create an instance of hashing
manager_rooms = {}

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


# Get customer information
def get_customer_info(email):
    connection, cursor = get_cursor()
    cursor.execute("SELECT * FROM customer WHERE email = %s", (email,))
    customer = cursor.fetchone()
    cursor.close()
    connection.close()
    return customer
# Manager manage orders

@manager_blueprint.route('/manage_orders', methods=['GET', 'POST'])
@role_required(['manager'])
def manage_orders():
    email = session.get('email')
    manager_info = get_manager_info(email)
    filter_status = request.args.get('status', 'active')
    search_email = request.args.get('search_email', '').strip()
    pickup_date = request.args.get('pickup_date', '').strip()
    sort_by = request.args.get('sort_by', 'order_id')  # Default sort by order_id
    sort_order = request.args.get('sort_order', 'asc')  # Default sort order ascending
    
    # Determine the next sort order for toggling
    next_sort_order = 'desc' if sort_order == 'asc' else 'asc'
    
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

    query += f" ORDER BY o.{sort_by} {sort_order.upper()}"

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
        return redirect(url_for('manager.manage_orders', status=filter_status, search_email=search_email, pickup_date=pickup_date, sort_by=sort_by, sort_order=sort_order))

    cursor.close()
    connection.close()

    return render_template('manager/manager_manage_orders.html', 
                           orders=orders, 
                           manager_info=manager_info, 
                           filter_status=filter_status, 
                           search_email=search_email, 
                           pickup_date=pickup_date, 
                           sort_by=sort_by, 
                           sort_order=sort_order, 
                           next_sort_order=next_sort_order)

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

# Manager search product
@manager_blueprint.route('/search_product', methods=['GET'])
@role_required(['manager'])
def search_product():
    email = session.get('email')
    manager_info = get_manager_info(email)
    product_name = request.args.get('product_name')
    connection, cursor = get_cursor()

    query = "SELECT product_id, name FROM product WHERE name LIKE %s"
    cursor.execute(query, ('%' + product_name + '%',))

    products = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('manager/manager_edit_inventory.html', manager_info=manager_info, products=products)

@manager_blueprint.route('/monitor_inventory')
@role_required(['manager'])
def monitor_inventory():
    email = session.get('email')
    manager_info = get_manager_info(email)
    page = request.args.get('page', 1, type=int)
    items_per_page = 10
    offset = (page - 1) * items_per_page
    category_filter = request.args.get('category')

    connection, cursor = get_cursor()

    # Query all categories except specific ones
    cursor.execute("""
        SELECT name FROM product_category 
        WHERE name NOT IN ('Coffee', 'Hot Drinks', 'Milkshakes', 'Iced Teas')
    """)
    categories = cursor.fetchall()
    categories = [row['name'] for row in categories]

    query = """
        SELECT
            product_category.name AS category,
            product.product_id,
            product.name,
            product.unit_price,
            product.description,
            product.is_available,
            product.image,
            inventory.quantity,
            inventory.last_updated,
            staff.first_name AS staff_first_name,
            staff.last_name AS staff_last_name,
            manager.first_name AS manager_first_name,
            manager.last_name AS manager_last_name
        FROM inventory
        LEFT JOIN product ON inventory.product_id = product.product_id
        LEFT JOIN product_category ON product.category_id = product_category.category_id
        LEFT JOIN staff ON inventory.staff_id = staff.staff_id
        LEFT JOIN manager ON inventory.manager_id = manager.manager_id
        WHERE product.is_available = 1
    """

    params = []
    if category_filter:
        query += " AND product_category.name = %s"
        params.append(category_filter)

    query += " ORDER BY product.name LIMIT %s OFFSET %s"
    params.extend([items_per_page, offset])

    cursor.execute(query, params)
    inventory = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('manager/manager_inventory.html', manager_info=manager_info, inventory=inventory, 
                           categories=categories, page=page, items_per_page=items_per_page, 
                           category=category_filter)

# Manager update inventory
@manager_blueprint.route('/update_inventory', methods=['POST'])
@role_required(['manager'])
def update_inventory():
    product_id = request.form.get('product_id')
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
    
# Handling product image add
@manager_blueprint.route('/upload_product_image', methods=["POST"])
@role_required(['manager'])
def handle_upload_product_image():
    if 'image' not in request.files:
        flash('No file part')
        return redirect(url_for('manager.manage_products'))

    file = request.files['image']

    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('manager.manage_products'))

    if len(file.filename) > MAX_FILENAME_LENGTH:
        flash('File name is too long')
        return redirect(url_for('manager.manage_products'))

    if file and allowed_file(file.filename):
        product_id = request.form.get('product_id')
        upload_product_image(product_id, file)
        flash('Product image successfully uploaded')
        return redirect(url_for('manager.manage_products'))
    else:
        flash('Invalid file type')
        return redirect(url_for('manager.manage_products'))

# Handling edit product image update
@manager_blueprint.route('/upload_product_image/<int:product_id>', methods=['POST'])
@role_required(['manager'])
def upload_product_image_new(product_id):
    if 'image' not in request.files:
        flash('No file part', 'error')
        return redirect(url_for('manager.edit_product', product_id=product_id))
    
    file = request.files['image']
    
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('manager.edit_product', product_id=product_id))

    if len(file.filename) > MAX_FILENAME_LENGTH:
        flash('File name is too long', 'error')
        return redirect(url_for('manager.edit_product', product_id=product_id))

    if file and allowed_file(file.filename):
        upload_product_image(product_id, file)
        flash('Product image successfully uploaded', 'success')
        return redirect(url_for('manager.edit_product', product_id=product_id))
    else:
        flash('Invalid file type', 'error')
        return redirect(url_for('manager.edit_product', product_id=product_id))
    
# Manager add new product
@manager_blueprint.route('/add_inventory', methods=['POST'])
@role_required(['manager'])
def add_inventory():
    category_id = request.form.get('category_id')
    name = request.form.get('name')
    description = request.form.get('description')
    unit_price = request.form.get('unit_price')
    quantity = request.form.get('quantity')
    option_type = request.form.get('option_type')
    option_name = request.form.get('option_name')
    additional_cost = request.form.get('additional_cost')
    image = request.files.get('image')
    connection, cursor = get_cursor()

    # Check if product with the same name already exists
    cursor.execute("SELECT * FROM product WHERE name = %s", (name,))
    existing_product = cursor.fetchone()
    if existing_product is not None:
        flash('A product with the same name already exists')
        connection.rollback()
        return redirect(url_for('manager.manage_products'))

    # Add the new product item to the database
    is_available = False
    cursor.execute("INSERT INTO product (category_id, name, description, unit_price, is_available) VALUES (%s, %s, %s, %s, %s)", (category_id, name, description, unit_price, is_available))

    # Get the product_id of the newly inserted product
    product_id = cursor.lastrowid

    # Upload product image if exists
    if image:
        upload_product_image(product_id, image)


    if option_type and option_name is not None:
        # Get the additional cost for the option
        cost = additional_cost.get(option_name, 0.00)
        
        cursor.execute("INSERT INTO product_option (product_id, option_type, option_name, additional_cost) VALUES (%s, %s, %s, %s)", 
                       (product_id, option_type, option_name, cost))
        option_id = cursor.lastrowid
    else:
        option_id = None

    # Get the category of the product
    cursor.execute("SELECT name FROM product_category WHERE category_id = %s", (category_id,))
    category = cursor.fetchone()['name']

    # Add the product to the inventory if it's not in the specified categories
    if category not in ["Coffee", "Milkshakes", "Iced Teas", "Hot Drinks"]:
        if option_id:
            cursor.execute("INSERT INTO inventory (product_id, option_id, quantity) VALUES (%s, %s, %s)", (product_id, option_id, quantity))
        else:
            cursor.execute("INSERT INTO inventory (product_id, quantity) VALUES (%s, %s)", (product_id, quantity))
    
    connection.commit()
    cursor.close()
    connection.close()

    flash('Product successfully added to inventory')
    return redirect(url_for('manager.manage_products'))


# Manager edit products
@manager_blueprint.route('/manage_products', methods=['GET'])
@role_required(['manager'])
def manage_products():
    email = session.get('email')
    manager_info = get_manager_info(email)
    page = request.args.get('page', 1, type=int)
    items_per_page = 10
    offset = (page - 1) * items_per_page
    category_filter = request.args.get('category_id')

    connection, cursor = get_cursor()

    cursor.execute("SELECT * FROM product_category")
    categories = cursor.fetchall()
    query = """
        SELECT
            product_category.name AS category,
            product.product_id,
            product.name,
            product.unit_price,
            product.description,
            product.image,
            product.is_available,
            GROUP_CONCAT(
                CASE 
                    WHEN product_option.option_type IN ('Add On', 'No Options') THEN ''
                    ELSE COALESCE(product_option.option_name, '')
                END SEPARATOR ', '
            ) AS options
        FROM product
        LEFT JOIN product_category ON product.category_id = product_category.category_id 
        LEFT JOIN product_option ON product.product_id = product_option.product_id
    """

    params = []
    if category_filter:
        query += " WHERE product.category_id = %s"
        params.append(category_filter)

    query += " GROUP BY product.product_id ORDER BY product.name LIMIT %s OFFSET %s"
    params.extend([items_per_page, offset])

    cursor.execute(query, params)
    products = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template('manager/manager_edit_product.html', 
                           products=products, 
                           categories=categories, 
                           manager_info=manager_info, 
                           page=page, 
                           items_per_page=items_per_page)


#option type
@manager_blueprint.route('/add_option_type', methods=['POST'])
@role_required(['manager'])
def add_option_type():
    option_type = request.form.get('option_type')
    option_names = request.form.getlist('option_name[]')
    additional_costs = request.form.getlist('additional_cost[]')

    connection, cursor = get_cursor()
    
    for option_name, additional_cost in zip(option_names, additional_costs):
        cursor.execute("""
            INSERT INTO product_option (option_type, option_name, additional_cost)
            VALUES (%s, %s, %s)
        """, (option_type, option_name, additional_cost))

    connection.commit()
    cursor.close()
    connection.close()

    flash('Option type and options successfully added.')
    return redirect(url_for('manager.manage_products'))


@manager_blueprint.route('/get_option_types', methods=['GET'])
@role_required(['manager'])
def get_option_types():
    connection, cursor = get_cursor()
    cursor.execute("SELECT DISTINCT option_type FROM product_option WHERE option_type != 'fruit flavour'")
    option_types = cursor.fetchall()
    connection.close()
    return jsonify({'option_types': [type['option_type'] for type in option_types]})

@manager_blueprint.route('/get_options_for_type', methods=['GET'])
@role_required(['manager'])
def get_options_for_type():
    option_type = request.args.get('type')
    connection, cursor = get_cursor()
    cursor.execute("""
        SELECT DISTINCT option_id, option_name, additional_cost 
        FROM product_option 
        WHERE option_type = %s
    """, (option_type,))
    options = cursor.fetchall()
    connection.close()

    return jsonify({'options': options})

    

@manager_blueprint.route('/edit_option_type', methods=['POST'])
@role_required(['manager'])
def edit_option_type():
    option_type = request.form.get('option_type')
    option_ids = request.form.getlist('option_id[]')
    option_names = request.form.getlist('edit_option_name[]')
    additional_costs = request.form.getlist('edit_additional_cost[]')

    connection, cursor = get_cursor()

    # Update existing options
    for option_id, option_name, additional_cost in zip(option_ids, option_names, additional_costs):
        cursor.execute("""
            UPDATE product_option
            SET option_name = %s, additional_cost = %s
            WHERE option_id = %s AND option_type = %s
        """, (option_name, additional_cost, option_id, option_type))

    # Add new options
    new_option_names = request.form.getlist('new_option_name[]')
    new_additional_costs = request.form.getlist('new_additional_cost[]')

    for option_name, additional_cost in zip(new_option_names, new_additional_costs):
        cursor.execute("""
            INSERT INTO product_option (option_type, option_name, additional_cost)
            VALUES (%s, %s, %s)
        """, (option_type, option_name, additional_cost))

    # Commit the additions and updates
    connection.commit()

   # Identify and remove deleted options
    existing_option_ids = set(int(id) for id in option_ids)
    cursor.execute("SELECT option_id FROM product_option WHERE option_type = %s", (option_type,))
    all_option_ids = {row['option_id'] for row in cursor.fetchall()}
    removed_option_ids = all_option_ids - existing_option_ids

    for option_id in removed_option_ids:
        cursor.execute("DELETE FROM product_option WHERE option_id = %s", (option_id,))


    connection.commit()
    cursor.close()
    connection.close()

    flash('Option types and options successfully updated.')
    return redirect(url_for('manager.manage_products'))

@manager_blueprint.route('/get_all_options', methods=['GET'])
@role_required(['manager'])
def get_all_options():
    connection, cursor = get_cursor()
    cursor.execute("""
        SELECT option_type, option_name, additional_cost 
        FROM product_option
        ORDER BY option_type, option_name
    """)
    options = cursor.fetchall()
    connection.close()
    options_dict = {}
    for option in options:
        if option['option_type'] not in options_dict:
            options_dict[option['option_type']] = []
        options_dict[option['option_type']].append({
            'option_name': option['option_name'],
            'additional_cost': option['additional_cost']
        })

    return jsonify({'options': options_dict})


@manager_blueprint.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@role_required(['manager'])
def edit_product(product_id):
    email = session.get('email')
    manager_info = get_manager_info(email)
    connection, cursor = get_cursor()

    cursor.execute("SELECT * FROM product_category")
    categories = cursor.fetchall()

    cursor.execute("SELECT DISTINCT option_type FROM product_option")
    option_types = cursor.fetchall()

    if request.method == 'POST':
        name = request.form.get('name')
        category_id = request.form.get('category_id')
        description = request.form.get('description')
        unit_price = request.form.get('unit_price')
        selected_option_types = request.form.getlist('option_types[]')

        cursor.execute("""
            UPDATE product 
            SET name = %s, category_id = %s, description = %s, unit_price = %s
            WHERE product_id = %s
        """, (name, category_id, description, unit_price, product_id,))

        cursor.execute("DELETE FROM product_option WHERE product_id = %s", (product_id,))
        
        for option_type in selected_option_types:
            cursor.execute("""
                SELECT DISTINCT option_name, additional_cost 
                FROM product_option 
                WHERE option_type = %s
            """, (option_type,))
            options = cursor.fetchall()
            
            for option in options:
                cursor.execute("""
                    INSERT INTO product_option (product_id, option_type, option_name, additional_cost)
                    SELECT %s, %s, %s, %s
                    FROM DUAL
                    WHERE NOT EXISTS (
                        SELECT 1 
                        FROM product_option 
                        WHERE product_id = %s AND option_type = %s AND option_name = %s
                    )
                """, (product_id, option_type, option['option_name'], option['additional_cost'], product_id, option_type, option['option_name']))

        connection.commit()
        connection.close()

        flash('Product updated successfully.', 'success')
        return redirect(url_for('manager.manage_products'))

    cursor.execute("""
        SELECT product.product_id, product.name, product.category_id, product_category.name AS category_name, 
               product.description, product.unit_price, product.image, COALESCE(GROUP_CONCAT(DISTINCT product_option.option_type), '') AS option_types
        FROM product 
        LEFT JOIN product_category ON product.category_id = product_category.category_id 
        LEFT JOIN product_option ON product.product_id = product_option.product_id
        WHERE product.product_id = %s
        GROUP BY product.product_id
    """, (product_id,))
    product = cursor.fetchone()

    if product:
        product['option_types'] = product['option_types'].split(',') if product['option_types'] else []
        cursor.execute("""
            SELECT option_type, option_name, additional_cost 
            FROM product_option
        """)
        all_options = cursor.fetchall() or []

        return render_template('manager/manager_edit_details.html', product=product, manager_info=manager_info, 
                               categories=categories, option_types=option_types, all_options=all_options)
    
    flash('Product not found.', 'error')
    return redirect(url_for('manager.manage_products'))


# Manager delete product
@manager_blueprint.route('/toggle_product_status/<int:product_id>', methods=['POST'])
@role_required(['manager'])
def toggle_product_status(product_id):
    connection, cursor = get_cursor()

    # Get the current status of the product
    cursor.execute("SELECT is_available FROM product WHERE product_id = %s", (product_id,))
    is_available = cursor.fetchone()['is_available']

    # Toggle the status
    new_status = not is_available
    cursor.execute("UPDATE product SET is_available = %s WHERE product_id = %s", (new_status, product_id,))
    connection.commit()

    cursor.close()
    connection.close()

    # Flash a success message
    if new_status:
        flash('Product has been activated.', 'success')
    else:
        flash('Product has been deactivated.', 'warning')

    return redirect(url_for('manager.manage_products', product_id=product_id))

# Manage accounts
@manager_blueprint.route('/manage_accounts', methods=['GET', 'POST'])
@role_required(['manager'])
def manage_accounts():
    email = session.get('email')
    manager_info = get_manager_info(email)
    role = request.args.get('role', 'customer')  # Default role set to 'customer'
    connection, cursor = get_cursor()
    
    base_query = """
         SELECT 'customer' as role, customer.customer_id AS id, customer.first_name, customer.last_name, customer.phone_number, 
             customer.date_of_birth, customer.gender, customer.id_num, customer.created_at, 
             customer.profile_image, customer.status, account.email, NULL as position
         FROM customer
         JOIN account ON customer.account_id = account.account_id
         UNION
         SELECT 'staff' as role, staff.staff_id AS id, staff.first_name, staff.last_name, staff.phone_number, 
             staff.date_of_birth, staff.gender, NULL as id_num, NULL as created_at, 
             staff.profile_image, staff.status, account.email, staff.position
         FROM staff
         JOIN account ON staff.account_id = account.account_id
         UNION
         SELECT 'manager' as role, manager.manager_id AS id, manager.first_name, manager.last_name, manager.phone_number, 
             manager.date_of_birth, manager.gender, NULL as id_num, NULL as created_at, 
             manager.profile_image, manager.status, account.email, manager.position
         FROM manager
         JOIN account ON manager.account_id = account.account_id
         WHERE account.email != %s
        """
    filters = [email]

    # Filter by role
    if role != 'all':
        base_query = f"""
            SELECT * FROM ({base_query}) AS all_roles WHERE role = %s
        """
        filters.append(role)

    # Search and filter accounts
    if request.method == 'POST':
        search_query = request.form.get('query')
        status = request.form.get('status')

        if search_query:
            search_query = f"%{search_query}%"
            base_query += " AND (first_name LIKE %s OR last_name LIKE %s OR email LIKE %s OR phone_number LIKE %s)"
            filters.extend([search_query, search_query, search_query, search_query])

        if status:
            base_query += " AND status = %s"
            filters.append(status)

    cursor.execute(base_query, filters)
    accounts = cursor.fetchall()

    cursor.close()
    connection.close()

    # Set the validation for birthday ages from 16-100
    today = date.today()
    min_date = (today - timedelta(days=365 * 100)).strftime('%Y-%m-%d')
    max_date = (today - timedelta(days=365 * 16)).strftime('%Y-%m-%d')

    return render_template('manager/manage_accounts.html', accounts=accounts, title=f"Manage {role.capitalize()}s", 
                           manager_info=manager_info, role=role, min_date=min_date, max_date=max_date)

# Manage edit account
@manager_blueprint.route('/edit_account/<account_id>/<role>', methods=['GET', 'POST'])
@role_required(['manager'])
def edit_account(account_id, role):
    connection, cursor = get_cursor()

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone_number = request.form.get('phone_number')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        id_num = request.form.get('id_num')
        position = request.form.get('position')

        try:
            if role == 'customer':
                cursor.execute("SELECT customer_id FROM customer WHERE customer_id = %s", (account_id,))
                customer_id = cursor.fetchone()['customer_id']
                cursor.execute("""
                    UPDATE customer 
                    SET first_name = %s, last_name = %s, phone_number = %s, date_of_birth = %s, gender = %s, id_num = %s
                    WHERE customer_id = %s
                """, (first_name, last_name, phone_number, date_of_birth, gender, id_num, customer_id))
            elif role == 'staff':
                cursor.execute("SELECT staff_id FROM staff WHERE staff_id = %s", (account_id,))
                staff_id = cursor.fetchone()['staff_id']
                cursor.execute("""
                    UPDATE staff 
                    SET first_name = %s, last_name = %s, phone_number = %s, date_of_birth = %s, gender = %s, position = %s
                    WHERE staff_id = %s
                """, (first_name, last_name, phone_number, date_of_birth, gender, position, staff_id))

            connection.commit()
            flash(f'{role.capitalize()} details updated successfully.', 'success')
        except Exception as e:
            connection.rollback()
            flash(f'Error updating {role} details: {str(e)}', 'error')
        finally:
            cursor.close()
            connection.close()

        return redirect(url_for('manager.manage_accounts', role=role))

    # Fetch the account details to pre-populate the form for GET request
    account_details = {}
    if role == 'customer':
        cursor.execute("SELECT * FROM customer WHERE customer_id = %s", (account_id,))
        account_details = cursor.fetchone()
    elif role == 'staff':
        cursor.execute("SELECT * FROM staff WHERE staff_id = %s", (account_id,))
        account_details = cursor.fetchone()

    cursor.close()
    connection.close()

    return render_template('manager/manage_accounts.html', account_details=account_details, role=role)

# Manager can add new staff
@manager_blueprint.route('/add_staff', methods=['POST'])
@role_required(['manager'])
def add_staff():
    email = request.form.get('email')
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    phone_number = request.form.get('phone_number')
    date_of_birth = request.form.get('date_of_birth')
    gender = request.form.get('gender')
    position = request.form.get('position')

    # validate
    if not email or not password or not first_name or not last_name or not phone_number or not date_of_birth or not gender or not position:
        flash('All fields are required.', 'error')
        return redirect(url_for('manager.manage_accounts', role='staff'))

    hashed_password = hashing.hash_value(password)
    default_image = '123.jpg'

    connection, cursor = get_cursor()

    try:
        # Add to account table
        cursor.execute("""
            INSERT INTO account (email, password, role)
            VALUES (%s, %s, 'staff')
        """, (email, hashed_password))
        account_id = cursor.lastrowid

        # Add to staff table
        cursor.execute("""
            INSERT INTO staff (account_id, first_name, last_name, phone_number, date_of_birth, gender, position, profile_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (account_id, first_name, last_name, phone_number, date_of_birth, gender, position, default_image))

        connection.commit()
        flash('New staff added successfully.', 'success')
    except Exception as e:
        connection.rollback()
        flash(f'Error adding new staff: {str(e)}', 'error')
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('manager.manage_accounts', role='staff'))

# Manager can add new manager
@manager_blueprint.route('/add_manager', methods=['POST'])
@role_required(['manager'])
def add_manager():
    email = request.form.get('email')
    password = request.form.get('password')
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    phone_number = request.form.get('phone_number')
    date_of_birth = request.form.get('date_of_birth')
    gender = request.form.get('gender')
    position = request.form.get('position')

    # validate
    if not email or not password or not first_name or not last_name or not phone_number or not date_of_birth or not gender or not position:
        flash('All fields are required.', 'error')
        return redirect(url_for('manager.manage_accounts', role='manager'))

    hashed_password = hashing.hash_value(password)
    default_image = '123.jpg'

    connection, cursor = get_cursor()

    try:
        # Add to account table
        cursor.execute("""
            INSERT INTO account (email, password, role)
            VALUES (%s, %s, 'manager')
        """, (email, hashed_password))
        account_id = cursor.lastrowid

        # Add to manager table
        cursor.execute("""
            INSERT INTO manager (account_id, first_name, last_name, phone_number, date_of_birth, gender, position, profile_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (account_id, first_name, last_name, phone_number, date_of_birth, gender, position, default_image))

        connection.commit()
        flash('New manager added successfully.', 'success')
    except Exception as e:
        connection.rollback()
        flash(f'Error adding new manager: {str(e)}', 'error')
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('manager.manage_accounts', role='manager'))

# Manager reset password
@manager_blueprint.route('/reset_password', methods=['POST'])
@role_required(['manager'])
def reset_password():
    account_id = request.form.get('account_id')
    role = request.form.get('role')

    # Generate a default password
    default_password = 'Password123.'
    salt = 'S1#e2!r3@t4$'
    hashed_password = hashing.hash_value(default_password, salt=salt)

    connection, cursor = get_cursor()

    try:
        # Debug information
        print(f'Account ID: {account_id}')
        print(f'Role: {role}')
        print(f'Hashed Password: {hashed_password}')

        if role == 'customer':
            cursor.execute("SELECT account_id FROM customer WHERE customer_id = %s", (account_id,))
        elif role == 'staff':
            cursor.execute("SELECT account_id FROM staff WHERE staff_id = %s", (account_id,))
        elif role == 'manager':
            cursor.execute("SELECT account_id FROM manager WHERE manager_id = %s", (account_id,))
        
        account_id_record = cursor.fetchone()
        print(f'Associated Account ID Record: {account_id_record}')
        
        if not account_id_record:
            raise Exception("Associated account ID not found.")

        actual_account_id = account_id_record['account_id']

        # Debug information
        cursor.execute("SELECT * FROM account WHERE account_id = %s", (actual_account_id,))
        account_record = cursor.fetchone()
        print(f'Account Record: {account_record}')

        cursor.execute("SELECT password FROM account WHERE account_id = %s", (actual_account_id,))
        current_password = cursor.fetchone()
        print(f'Current Password: {current_password}')

        cursor.execute("UPDATE account SET password = %s WHERE account_id = %s", (hashed_password, actual_account_id))
        connection.commit()

        cursor.execute("SELECT password FROM account WHERE account_id = %s", (actual_account_id,))
        new_password = cursor.fetchone()
        print(f'New Password: {new_password}')

        flash(f'{role.capitalize()} password has been reset successfully.', 'success')
    except Exception as e:
        connection.rollback()
        flash(f'Error resetting password: {str(e)}', 'error')
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('manager.manage_accounts', role=role))

# Manager toggle account status
@manager_blueprint.route('/toggle_status', methods=['POST'])
@role_required(['manager'])
def toggle_status():
    account_id = request.form.get('account_id')
    role = request.form.get('role')

    connection, cursor = get_cursor()

    try:
        # 根据角色获取当前状态
        if role == 'customer':
            cursor.execute("SELECT status FROM customer WHERE customer_id = %s", (account_id,))
        elif role == 'staff':
            cursor.execute("SELECT status FROM staff WHERE staff_id = %s", (account_id,))
        elif role == 'manager':
            cursor.execute("SELECT status FROM manager WHERE manager_id = %s", (account_id,))
        
        current_status = cursor.fetchone()['status']
        new_status = 'inactive' if current_status == 'active' else 'active'

        # 更新状态
        if role == 'customer':
            cursor.execute("UPDATE customer SET status = %s WHERE customer_id = %s", (new_status, account_id))
        elif role == 'staff':
            cursor.execute("UPDATE staff SET status = %s WHERE staff_id = %s", (new_status, account_id))
        elif role == 'manager':
            cursor.execute("UPDATE manager SET status = %s WHERE manager_id = %s", (new_status, account_id))

        connection.commit()
        flash(f'{role.capitalize()} status has been changed to {new_status}.', 'success')
    except Exception as e:
        connection.rollback()
        flash(f'Error toggling status: {str(e)}', 'error')
    finally:
        cursor.close()
        connection.close()

    return redirect(url_for('manager.manage_accounts', role=role))

@manager_blueprint.route('/manage_accommodation', methods=['GET', 'POST'])
@role_required(['manager'])
def manage_accommodation():
    connection, cursor = get_cursor()
    try:
        if request.method == 'POST':
            action = request.form['action']
            accommodation_id = request.form['accommodation_id']
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
            manager_id = session.get('id')

            if end_date < start_date:
                flash('End date must be later than start date.', 'danger')
            else:
                if action == 'block':
                    # Insert blocked dates into the database
                    cursor.execute("""
                        INSERT INTO blocked_dates (accommodation_id, start_date, end_date, is_active, manager_id)
                        VALUES (%s, %s, %s, TRUE, %s)
                    """, (accommodation_id, start_date, end_date, manager_id))
                    connection.commit()
                    flash('Dates successfully blocked.', 'success')
                elif action == 'unblock':
                    # Update blocked dates to inactive
                    cursor.execute("""
                        UPDATE blocked_dates
                        SET is_active = FALSE, manager_id = %s
                        WHERE accommodation_id = %s AND start_date = %s AND end_date = %s
                    """, (manager_id, accommodation_id, start_date, end_date))
                    connection.commit()
                    flash('Dates successfully unblocked.', 'success')

        # Fetch accommodations for the dropdown
        cursor.execute("SELECT * FROM accommodation")
        accommodations = cursor.fetchall()

        # Fetch current blocked dates (only the latest status for each date range)
        cursor.execute("""
            SELECT bd.*, a.type, m.first_name, m.last_name
            FROM blocked_dates bd
            JOIN accommodation a ON bd.accommodation_id = a.accommodation_id
            LEFT JOIN manager m ON bd.manager_id = m.manager_id
            WHERE bd.is_active = TRUE
            AND bd.block_id = (SELECT MAX(block_id) FROM blocked_dates WHERE accommodation_id = bd.accommodation_id AND start_date = bd.start_date AND end_date = bd.end_date)
            ORDER BY bd.start_date ASC
        """)
        current_blocked_dates = cursor.fetchall()

        # Fetch blocked dates history (include all dates)
        cursor.execute("""
            SELECT bd.*, a.type, m.first_name, m.last_name
            FROM blocked_dates bd
            JOIN accommodation a ON bd.accommodation_id = a.accommodation_id
            LEFT JOIN manager m ON bd.manager_id = m.manager_id
            ORDER BY bd.start_date ASC
        """)
        blocked_dates_history = cursor.fetchall()

    except Exception as e:
        print("Error: ", str(e))
        flash('An error occurred while managing accommodation.', 'danger')
    finally:
        cursor.close()
        connection.close()

    return render_template('manager/manage_accommodation.html', accommodations=accommodations, current_blocked_dates=current_blocked_dates, blocked_dates_history=blocked_dates_history)

# Chat room for managers

def get_chat_history_for_manager_and_customer(customer_id):
    connection, cursor = get_cursor()
    cursor.execute("""
        SELECT content, sent_at, sender_type, staff_id, manager_id, customer_id
        FROM message
        WHERE customer_id = %s
        ORDER BY sent_at ASC
    """, (customer_id,))
    messages = cursor.fetchall()
    cursor.close()
    connection.close()
    return messages


@manager_blueprint.route('/chat/<int:customer_id>')
@role_required(['manager'])
def manager_chat(customer_id):
    email = session.get('email')
    manager_info = get_manager_info(email)
    customer_info = get_customer_info_by_id(customer_id)
    chat_history = get_chat_history_for_manager_and_customer(customer_id)
    return render_template('manager/manager_chat.html', manager_info=manager_info, customer_info=customer_info, chat_history=chat_history)

@manager_blueprint.route('/customers')
@role_required(['manager'])
def list_customers():
    connection, cursor = get_cursor()
    cursor.execute("SELECT customer_id, first_name, last_name FROM customer")
    customers = cursor.fetchall()
    cursor.close()
    connection.close()
    return render_template('manager/manager_list_customers.html', customers=customers, manager_info=get_manager_info(session.get('email')))
@socketio.on('message', namespace='/manager')
def handle_message_manager(data):
    user_id = data.get('user_id')
    message = data.get('message')
    room = data.get('room')
    
    manager_id = user_id
    customer_id = data.get('partner_id')
    
    connection, cursor = get_cursor()
    try:
        cursor.execute("""
            INSERT INTO message (manager_id, customer_id, sender_type, content, sent_at) VALUES (%s, %s, 'manager', %s, NOW())
        """, (manager_id, customer_id, message))
        connection.commit()

        cursor.execute("SELECT message_id, sent_at FROM message WHERE message_id = LAST_INSERT_ID()")
        msg_data = cursor.fetchone()
        sent_at = msg_data['sent_at']
        message_id = msg_data['message_id']
    except Exception as e:
        print(f"Error saving message: {e}")
        connection.rollback()
    finally:
        cursor.close()
        connection.close()
    
    if room:
        send({
            'message_id': message_id,
            'message': message,
            'user_type': 'manager',
            'username': 'Manager',
            'sent_at': sent_at.strftime('%d-%m-%Y %H:%M:%S'),
            'manager_id': manager_id
        }, to=room, namespace='/manager')

@manager_blueprint.route('/chat_history/<int:customer_id>')
@role_required(['manager'])
def get_chat_history_manager(customer_id):
    email = session.get('email')
    manager_info = get_manager_info(email)
    manager_id = manager_info['manager_id']

    messages = get_chat_history_for_manager_and_customer(customer_id)

    return jsonify(messages)
