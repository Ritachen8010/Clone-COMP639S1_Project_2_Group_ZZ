from flask import Flask
from auth import auth_blueprint
from guest import guest_blueprint
from manager import manager_blueprint
from staff import staff_blueprint
from customer import customer_blueprint
from flask_hashing import Hashing

app = Flask(__name__)

app.secret_key = 'Group ZZ'

hashing = Hashing(app)

app.register_blueprint(auth_blueprint)
app.register_blueprint(guest_blueprint)
app.register_blueprint(manager_blueprint, url_prefix='/manager') 
app.register_blueprint(staff_blueprint, url_prefix='/staff') 
app.register_blueprint(customer_blueprint, url_prefix='/customer') 


if __name__=='__main__':

    app.run(debug=True)