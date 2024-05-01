from flask import Blueprint, render_template, redirect, url_for,\
    session, request, flash, jsonify
from flask_hashing import Hashing
from config import get_cursor, allowed_file,UPLOAD_FOLDER
from auth import role_required
import re
import os
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
#from flask_sqlalchemy import SQLAlchemy

# create manager blueprint view
manager_blueprint = Blueprint('manager', __name__)
#create an instance of hashing
hashing = Hashing()


@manager_blueprint.route('/')
@role_required(['manager'])
def manager():
    return render_template(' manager/manager_dashboard.html') 
