from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, \
    abort, session, Response, current_app, send_from_directory
import bcrypt
from wsh_models import sess, Users, login_manager, Oura_token, Locations, \
    Weather_history, User_location_day
from flask_login import login_required, login_user, logout_user, current_user
import requests
from app_package.users.utils import oura_sleep_call, oura_sleep_db_add, \
    add_db_locations, weather_api_call, add_db_weather_hist, db_add_user_loc_day
from sqlalchemy import func
from datetime import datetime

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
    
    print('current_user stuff:')
    print(current_user.lat, ", ", current_user.lon)

    print('current_user.lat:', current_user.lat)
    print(type(current_user.lat))

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
        formDict = request.form.to_dict()
 
        if formDict.get('oura_token') != existing_oura_token_str:

            new_token=formDict.get('oura_token')
            if new_token != '':
                #if new token is NOT blank
                #--1)update token
                add_new_token = Oura_token(token=formDict.get('oura_token'), user_id=current_user.id)
                sess.add(add_new_token)
                sess.commit()

                #--2)make oura api          
                sleep_dict = oura_sleep_call(new_token = new_token)
                if sleep_dict == 'Error with Token':
                    flash('Error with Token')
                    return redirect(url_for('users.account'))

                #--3)store date in database
                
                oura_sleep_db_add(sleep_dict, add_new_token.id)

                #-- 4) get oldest oura sleep date

                #-- 5) check if location exists

                #-- 6) if location exists make api call for all dates wh

                return redirect(url_for('users.account'))
            
            else: # token is blank commit blank token
                new_token = Oura_token(token=formDict.get('oura_token'), user_id=current_user.id)
                sess.add(new_token)
                sess.commit()

                return redirect(url_for('users.account'))
        
        if (formDict.get('location_text') != existing_coordinates) or (
            formDict.get('location_text')!='' and existing_coordinates == ''):
            print('****** Updating User location ******')
            min_loc_distance_difference = 1000
            if formDict.get('location_text') != '':# Location is not null needs update
              
                user.lat = formDict.get('location_text').split(',')[0]
                user.lon = formDict.get('location_text').split(',')[1]
                sess.commit()

                # location_search = sess.query(Locations).filter_by

                #1) Check Locations table to see if user's location already exists or close enough (.1 degree)
                locations_unique_list = sess.query(Locations).all()
                for loc in locations_unique_list:
                    lat_diff = abs(user.lat - loc.lat)
                    lon_diff = abs(user.lon - loc.lon)
                    loc_dist_diff = lat_diff + lon_diff
                    print('** Differences **')
                    print('lat_difference:', lat_diff)
                    print('lon_diff:', lon_diff)

                    if loc_dist_diff < min_loc_distance_difference:
                        print('-----> loc_dist_diff is less than min required')
                        min_loc_distance_difference = loc_dist_diff
                        location_id = loc.id

                if min_loc_distance_difference < .1:
                    print('**** min_loc_distance diff < .1 ***** FIRED ***')
                    # if already exists row for user_loc_day today and location id don't add
                    search_user_loc_day = sess.query(User_location_day).filter_by(
                        location_id = location_id,
                        user_id = current_user.id,
                        date = datetime.today().strftime('%Y-%m-%d')
                    ).first()
                    if search_user_loc_day:
                        print('User_loc_day alreay has entry no need to add another.')
                    else:
                        #2a) Existing location is close enough
                        # no api call needee
                        # add User_location_day get the latest temperature
                        # 1a) get today's weather history
                        today_weather = sess.query(Weather_history).filter_by(
                            location_id = location_id, 
                            date = datetime.today().strftime('%Y-%m-%d')
                        ).first()

                        avgtemp_f = today_weather.avgtemp_f
                        if today_weather:
                            user_loc_day_id = db_add_user_loc_day(avgtemp_f, location_id)

                        print('*** No Weather API call, Locatoin or weather histry added')

                else:
                    print('**** min_loc_distance difff did NOT fire *****')
                    #2b) No existing location near enough
                    # make weather api call to get location
                    weather_dict = weather_api_call()

                    #3) add row locations
                    location_id = add_db_locations(weather_dict)
                    print('Successfully added location_id: ', location_id)

                    #4) Add to weather_hist row
                    weather_hist_id = add_db_weather_hist(weather_dict, location_id)
                    print('Successfully added weather_hist_id: ', weather_hist_id)

                    avgtemp_f = weather_dict.get('forecast').get('forecastday')[0].get('day').get('avgtemp_f')
                    user_loc_day_id = db_add_user_loc_day(avgtemp_f, location_id)
                    print('Successfully added user_loc_day_id: ', user_loc_day_id)

            else:# Blank out user lat and lon
                user.lat = None
                user.lon = None
                sess.commit()
                print('**** NO weather API call *****')

            return redirect(url_for('users.account'))
        else:
            print('**** NOT update location ***')
            
    
    return render_template('account.html', page_name = page_name, email=email,
         oura_token = oura_token, location_coords = existing_coordinates)