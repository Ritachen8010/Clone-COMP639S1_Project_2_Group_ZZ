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
 

@staff_blueprint.route('/')
@role_required(['staff'])
def staff():
    return render_template('staff/staff_dashboard.html',active='dashboard') 
