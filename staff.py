from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash, jsonify
from flask_hashing import Hashing
from config import get_cursor, allowed_file, UPLOAD_FOLDER
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
