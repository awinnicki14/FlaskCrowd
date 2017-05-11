from flask import Flask, jsonify, request, render_template, redirect, url_for, session
from sqlalchemy.orm.session import sessionmaker, make_transient
from sqlalchemy import create_engine
from database import db
from page_model_opt import PageModel
import glob
import os 
import random
import numpy as np
from cython_tste.tste_next_point import *
import time
import hashlib




print "Hello"

# Choose a random triplet and set the page's triplet accordingly

def update_page_with_random():
    page_ims = random.sample(range(len(image_list)), 3)

    page_model_dict[session['name']].main_img = page_ims[0]
    page_model_dict[session['name']].compare_img_1 = page_ims[1]
    page_model_dict[session['name']].compare_img_2 = page_ims[2]

    page_model_dict[session['name']].main_path = image_list[page_ims[0]]
    page_model_dict[session['name']].compare_1_path = image_list[page_ims[1]]
    page_model_dict[session['name']].compare_2_path = image_list[page_ims[2]]





# Make Flask app

app = Flask(__name__)
app.config["DEBUG"] = True




# Set up database

SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://{username}:{password}@{hostname}/{databasename}".format(
    username="cs101teaching",
    password="gogo_teaching",
    hostname="cs101teaching.mysql.pythonanywhere-services.com",
    databasename="cs101teaching$teaching",
)
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_POOL_RECYCLE"] = 200
app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'

db.init_app(app)
db.app = app

engine = create_engine(SQLALCHEMY_DATABASE_URI, pool_recycle=200)

Session_sql = sessionmaker(bind=engine, expire_on_commit=False)
session_sql = Session_sql()



# Make image list

image_list = glob.glob("/home/cs101teaching/MachineTeaching/static/oct/data_resized/*/*")
image_list.sort()

image_list = [img.replace("/home/cs101teaching/MachineTeaching", "") for img in image_list]


# Make dictionary to keep track of page models
page_model_dict = {}



# Make dictionary to keep track of how many jobs each user has done
user_nclicks_dict = {}
user_id_dict = {}
user_time_dict = {}
user_code_dict = {}



# Set triplet

random.seed()
counter = 0
max_clicks = 50



# Redirect user to login page

@app.route("/")
def to_login():
    return redirect(url_for('login'))

# Return image list in JSON format 

@app.route("/get_imgs")
def get_imgs():
    return jsonify(page_model_dict[session['name']].get_imgs_list() + [str(user_nclicks_dict[session['name']])]) 

@app.route("/end/")
def logout():
    if ('name' in session and session['name'] in user_nclicks_dict and 
        user_nclicks_dict[session['name']] == max_clicks):
            # end_id = session['name']
            end_id = hashlib.md5(str(session['name'])).hexdigest()
            # print end_id
            return render_template('end.html', end_id=end_id)
    else:
        return redirect(url_for('login'))


# THESE DO LOTS
#
# - Gets the response from the user
# - Updates the user's kernel

@app.route("/kernel/get_response", methods = ['POST'])
def get_response_kernel():
    if not 'name' in session or not session['name'] in user_nclicks_dict:
        return jsonify([url_for('login'), 0])
    if request.method == 'POST':
        data = request.get_data()
        if data == "0":
            page_model_dict[session['name']].set_chosen(page_model_dict[session['name']].compare_img_1)
        elif data == "1":
            page_model_dict[session['name']].set_chosen(page_model_dict[session['name']].compare_img_2)
        user_nclicks_dict[session['name']] += 1
        user_time_dict[session['name']][1] = time.time()

        if user_nclicks_dict[session['name']] == max_clicks: 
            return jsonify([url_for('logout'), 0])

    make_transient(page_model_dict[session['name']])
    page_model_dict[session['name']].id = None
    session_sql.add(page_model_dict[session['name']])
    session_sql.commit()

    update_page_with_random()
    return jsonify(page_model_dict[session['name']].get_imgs_list() + [str(user_nclicks_dict[session['name']])])



# Render main page

@app.route("/kernel/")
def kernel_index():
    if not 'name' in session or not session['name'] in user_nclicks_dict:
        return redirect(url_for('login'))
    return render_template('kernel.html')



# Create new user
#
# - Store given user name
# - Create initial kernel for new user

@app.route('/login', methods=['GET', 'POST'])
def login(): 
    global counter 

    error = None
    if request.method == 'POST' and request.form['cont'] == "Continue":
        np.save('nclicks_dict.npy', user_nclicks_dict)
        np.save('time_dict.npy', user_time_dict)
        np.save('code_dict.npy', user_code_dict)
        session['name'] = counter
        counter += 1
        page_model_dict[session['name']] = PageModel()
        update_page_with_random()
        user_nclicks_dict[session['name']] = 0
        user_time_dict[session['name']] = [time.time(), 0]

        return redirect(url_for('kernel_index'))
    return render_template('login_rand.html', error=error)


# Run
if __name__ == "__main__":
app.run()
