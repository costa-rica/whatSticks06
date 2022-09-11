from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, \
    abort, session, Response, current_app, send_from_directory
import bcrypt
from wsh_models import sess, Users, login_manager, Oura_token, Locations, \
    Weather_history, User_location_day
from flask_login import login_required, login_user, logout_user, current_user
import requests
from app_package.users.utils import oura_sleep_call, oura_sleep_db_add, \
    add_db_locations, weather_api_call, add_db_weather_hist, db_add_user_loc_day, \
    location_exists
    
from sqlalchemy import func
from datetime import datetime
import time

salt = bcrypt.gensalt()


users = Blueprint('users', __name__)

@users.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        formDict = request.form.to_dict()
        if formDict.get('login'):
            return redirect(url_for('users.login'))
        elif formDict.get('register'):
            return redirect(url_for('users.register'))

    return render_template('home.html')

@users.route('/login', methods = ['GET', 'POST'])
def login():
    print('* in login *')
    page_name = 'Login'
    if request.method == 'POST':
        formDict = request.form.to_dict()
        email = formDict.get('email')
        print('email from webstie:::', email)

        user = sess.query(Users).filter_by(email=email).first()
        print('user for logging in:::', user)
        # verify password using hash
        password = formDict.get('password_text')
        if user:
            if password:
                if bcrypt.checkpw(password.encode(), user.password):
                    print("match")
                    login_user(user)
                    flash('Logged in succesfully')
                    # next = request.args.get('next')
                    # if not is_safe_url(next):
                    #     return flask.abort(400)
                    return redirect(url_for('dash.dashboard'))
                else:
                    print("does not match")
            else:
                print('No password ****')
        else:
            flash('No user by that name')

        # if successsful login_something_or_other...


    
    return render_template('login.html', page_name = page_name)

@users.route('/register', methods = ['GET', 'POST'])
def register():
    page_name = 'Register'
    if request.method == 'POST':
        formDict = request.form.to_dict()
        hash_pw = bcrypt.hashpw(formDict.get('password_text').encode(), salt)
        new_user = Users(email = formDict.get('email'), password = hash_pw)
        sess.add(new_user)
        sess.commit()
        return redirect(url_for('users.login'))

    return render_template('login.html', page_name = page_name)



@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('users.login'))


@users.route('/account', methods = ['GET', 'POST'])
@login_required
def account():
    page_name = 'Account Page'
    email = current_user.email

    existing_oura_token =sess.query(Oura_token, func.max(
        Oura_token.id)).filter_by(user_id=current_user.id).first()[0]
    
    # print('current_user stuff:')
    # print(current_user.lat, ", ", current_user.lon)

    # print('current_user.lat:', current_user.lat)
    # print(type(current_user.lat))

    user = sess.query(Users).filter_by(id = current_user.id).first()
    


    if user.lat == None or user.lat == '':
        existing_coordinates = ''
    else:
        existing_coordinates = f'{user.lat}, {user.lon}'
        
    
    if existing_oura_token:
        oura_token = current_user.oura_token_id[-1].token
        existing_oura_token_str = str(existing_oura_token.token)
    else:
        oura_token = ''
        existing_oura_token_str = ''



    if request.method == 'POST':
        startTime_post = time.time()
        formDict = request.form.to_dict()
 

        #1) User adds Oura_token data
            #a cases oura_token was blank and not it is not
            #b case oura_token was not blank and not it is different than before
        new_token = formDict.get('oura_token')
        new_location = formDict.get('location_text')
        if new_token != existing_oura_token_str:#<-- if new token is different 

            #1-1) add token to Oura_token
            print('* --> start oura_ring token data process')
            add_new_token = Oura_token(token = new_token, user_id=current_user.id)
            sess.add(add_new_token)
            sess.commit()

            if new_token != '':#<-- if new token is not blank make api call
                #1-2) call oura_ring api with new token
                sleep_dict = oura_sleep_call(new_token = new_token)
                if sleep_dict == 'Error with Token':
                    flash('Error with token api call - verify token was typed in correctly')
                    return redirect(url_for('users.account'))

                #1-3) add oura data to Oura_sleep_descriptions
                oura_sleep_db_add(sleep_dict, add_new_token.id)
                #TODO: this step works but is really slow
        

        #2) User adds location data
            #a case location was blank and now it is not anymore
            #b case location is different than it was before

        if new_location != existing_coordinates:
            print('* --> start location data process')

            #2-1) update users location in Users
            user = sess.query(Users).filter_by(id = current_user.id).first()
            
            if new_location == '':
                user.lat = None
                user.lon = None
                sess.commit()
            
            else:#<-- location has latitude and longitude
                user.lat = formDict.get('location_text').split(',')[0]
                user.lon = formDict.get('location_text').split(',')[1]
                sess.commit()

                #2-2) check locations
                location_id = location_exists(user)

                if location_id == 0:#<-- add new location
                    
                
                #2-2) call weather api to get location data
                    weather_dict = weather_api_call()

                #2-3) add location dat to Locations table
                    #-- make sure location is new .. use >.1 deg script
                    location_id = add_db_locations(weather_dict)


        #END of POST
        executionTime = (time.time() - startTime_post)
        print('POST time in seconds: ' + str(executionTime))
        return redirect(url_for('users.account'))
            
    
    return render_template('account.html', page_name = page_name, email=email,
         oura_token = oura_token, location_coords = existing_coordinates)