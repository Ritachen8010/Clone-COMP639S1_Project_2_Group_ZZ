import connect
import mysql.connector
import os
#accept image type when uploading  images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
#the folder for the uploaded images, this is for the local app
UPLOAD_FOLDER = 'static/images/'


dbconn = None
connection = None
# connect with database, and get the cursor function
def get_cursor():
    global dbconn
    global connection
    connection = mysql.connector.connect(user=connect.dbuser, \
    password=connect.dbpass, host=connect.dbhost,\
    database=connect.dbname, autocommit=True)
    dbconn = connection.cursor(dictionary=True)
    return connection, dbconn  # return both connection and cursor

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_image_exist(image_name):
    # Construct the full path to the image file
    image_path = os.path.join(UPLOAD_FOLDER, image_name)
    # Check if the file exists
    if os.path.exists(image_path):
        return True
    else:
        return False
    