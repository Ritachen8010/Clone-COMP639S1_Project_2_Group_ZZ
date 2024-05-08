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
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = 'bright.tech.ap@gmail.com'  
app.config["MAIL_PASSWORD"] = 'xupijwvjmgygqljg'
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True

mail = Mail(app)

@guest_blueprint.route('/')
def home():
    return render_template('home/guest.html')

@guest_blueprint.route('/about_us')
def about_us():
    return render_template('home/about_us.html')

class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(message="Please enter your name.")])
    email = StringField("Email", validators=[DataRequired(message="Please enter your email address"), Email()])
    subject = StringField("Subject", validators=[DataRequired(message="Please enter a subject.")])
    message = TextAreaField("Message", validators=[DataRequired(message="Please enter a message.")])
    submit = SubmitField("Send")


@guest_blueprint.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if request.method == 'POST' and form.validate_on_submit():

        msg = Message(form.subject.data, sender='bright.tech.ap@gmail.com', recipients=['bright.tech.ap@gmail.com'])
        msg.body = f"""
        From: {form.name.data} <{form.email.data}>
        {form.message.data}
        """
        print("Subject:", msg.subject)  
        print("Body:", msg.body)       
        mail.send(msg)
        
        flash('Your message has been sent successfully!', 'success')


        return render_template('contact_success.html', form=form, success=True)
    
    return render_template('home/about_us.html', form=form, success=False)

@guest_blueprint.route('/get-coffee-and-hot-drinks')
def get_coffee_and_hot_drinks():
    _, cursor = get_cursor() 
    try:
        cursor.execute("SELECT name, description, unit_price, image FROM product WHERE category_id IN (1, 2)")
        products = cursor.fetchall()
        product_list = []
        for product in products:
            product_dict = {
                'name': product['name'],       
                'description': product['description'],
                'price': product['unit_price'],
                'image': f"{product['image']}"
            }
            product_list.append(product_dict)
    except Exception as e:
        cursor.close()  
        print(f"Error: {e}")
        return jsonify({"error": "Failed to fetch products"}), 500
    finally:
        cursor.close() 

    return jsonify(product_list)


@guest_blueprint.route('/get_cold_drinks')
def get_cold_drinks():
    _, cursor = get_cursor() 
    try:
        cursor.execute("SELECT name, description, unit_price, image FROM product WHERE category_id IN (3, 5)")
        products = cursor.fetchall()
        product_list = []
        for product in products:
            product_dict = {
                'name': product['name'],       
                'description': product['description'],
                'price': product['unit_price'],
                'image': f"{product['image']}"
            }
            product_list.append(product_dict)
    except Exception as e:
        cursor.close()  
        print(f"Error: {e}")
        return jsonify({"error": "Failed to fetch products"}), 500
    finally:
        cursor.close() 

    return jsonify(product_list)


@guest_blueprint.route('/get_milkshake')
def get_milkshake():
    _, cursor = get_cursor() 
    try:
        cursor.execute("SELECT name, description, unit_price, image FROM product WHERE category_id = 4")
        products = cursor.fetchall()
        product_list = []
        for product in products:
            product_dict = {
                'name': product['name'],       
                'description': product['description'],
                'price': product['unit_price'],
                'image': f"{product['image']}"
            }
            product_list.append(product_dict)
    except Exception as e:
        cursor.close()  
        print(f"Error: {e}")
        return jsonify({"error": "Failed to fetch products"}), 500
    finally:
        cursor.close() 

    return jsonify(product_list)

@guest_blueprint.route('/quicktaste')
def quicktaste():
    _, cursor = get_cursor() 
    try:
        cursor.execute("SELECT name, description, unit_price, image FROM product WHERE category_id = 6")
        products = cursor.fetchall()
        product_list = []
        for product in products:
            product_dict = {
                'name': product['name'],       
                'description': product['description'],
                'price': product['unit_price'],
                'image': f"{product['image']}"
            }
            product_list.append(product_dict)
    except Exception as e:
        cursor.close()  
        print(f"Error: {e}")
        return jsonify({"error": "Failed to fetch products"}), 500
    finally:
        cursor.close() 

    return jsonify(product_list)

@guest_blueprint.route('/chill')
def chill():
    _, cursor = get_cursor() 
    try:
        cursor.execute("SELECT name, description, unit_price, image FROM product WHERE category_id = 7")
        products = cursor.fetchall()
        product_list = []
        for product in products:
            product_dict = {
                'name': product['name'],       
                'description': product['description'],
                'price': product['unit_price'],
                'image': f"{product['image']}"
            }
            product_list.append(product_dict)
    except Exception as e:
        cursor.close()  
        print(f"Error: {e}")
        return jsonify({"error": "Failed to fetch products"}), 500
    finally:
        cursor.close() 

    return jsonify(product_list)

@guest_blueprint.route('/essektials')
def essektials():
    _, cursor = get_cursor() 
    try:
        cursor.execute("SELECT name, description, unit_price, image FROM product WHERE category_id = 8")
        products = cursor.fetchall()
        product_list = []
        for product in products:
            product_dict = {
                'name': product['name'],       
                'description': product['description'],
                'price': product['unit_price'],
                'image': f"{product['image']}"
            }
            product_list.append(product_dict)
    except Exception as e:
        cursor.close()  
        print(f"Error: {e}")
        return jsonify({"error": "Failed to fetch products"}), 500
    finally:
        cursor.close() 

    return jsonify(product_list)