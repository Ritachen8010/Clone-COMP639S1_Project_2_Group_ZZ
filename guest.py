from flask import Flask, render_template, Blueprint, request, flash, jsonify
from auth import auth_blueprint
from config import get_cursor
from flask_wtf import FlaskForm
from datetime import datetime,date,timedelta
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email
from flask_mail import Mail, Message

app = Flask(__name__)

guest_blueprint = Blueprint('guest', __name__)


@guest_blueprint.route('/')
def home():
    return render_template('guest.html')
