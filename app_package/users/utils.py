from flask import current_app, url_for
from flask_login import current_user
import json
import requests
from datetime import datetime, timedelta
from wsh_models import sess, Users, Locations, Weather_history, \
    Oura_token, Oura_sleep_descriptions, User_location_day
import time
from flask_mail import Message
from app_package import mail
from wsh_config import ConfigDev

config = ConfigDev()

def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender=config.MAIL_USERNAME,
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}

If you did not make this request, ignore email and there will be no change
'''

    mail.send(msg)


def send_confirm_email(email):
    msg = Message('Registration Confirmation',
        sender=current_app.config['MAIL_USERNAME'],
        recipients=[email])
    msg.body = 'You have succesfully been registered to What-Sticks.'
    mail.send(msg)



def call_weather_api(user):
#2-1b-1) call weather API
    api_token = current_app.config['WEATHER_API_KEY']
    # base_url = 'http://api.weatherapi.com/v1'#TODO: put this address in config
    base_url = current_app.config['WEATHER_API_URL_BASE']
    history = '/history.json'#TODO: put this address in config
    payload = {}
    payload['q'] = f"{user.lat}, {user.lon}"
    payload['key'] = api_token
    yesterday = datetime.today() - timedelta(days=1)
    payload['dt'] = yesterday.strftime('%Y-%m-%d')
    payload['hour'] = 0

#2-1b) if new location is new add location to Locations
    print('* --> start location data process')
    new_location = Locations()
    try:
        r_history = requests.get(base_url + history, params = payload)
        
        if r_history.status_code == 200:
        
            #2) for each id call weather api
            return r_history.json()
        else:
            return f'Problem connecting with Weather API. Response code: {r_history.status_code}'
    except:
        return 'Error making call to Weather API. No response.'


def add_weather_history(weather_api_response, location_id):
    forecast = weather_api_response.get('forecast').get('forecastday')[0]
    
    row_exists = sess.query(Weather_history).filter_by(
        location_id= location_id,
        date = forecast.get('date')).first()

    if not row_exists:
        weather_hist_temp = {}
        # Get location stuff
        weather_hist_temp['city_location_name'] = weather_api_response.get('location').get('name')
        weather_hist_temp['region_name'] = weather_api_response.get('location').get('region')
        weather_hist_temp['country_name'] = weather_api_response.get('location').get('country')
        weather_hist_temp['lat'] = weather_api_response.get('location').get('lat')
        weather_hist_temp['lon'] = weather_api_response.get('location').get('lon')
        weather_hist_temp['tz_id'] = weather_api_response.get('location').get('tz_id')
        weather_hist_temp['location_id'] = location_id 
        
        #Get temperature stuff
        weather_hist_temp['date']= forecast.get('date')
        weather_hist_temp['maxtemp_f']= forecast.get('day').get('maxtemp_f')
        weather_hist_temp['mintemp_f']= forecast.get('day').get('mintemp_f')
        weather_hist_temp['avgtemp_f']= forecast.get('day').get('avgtemp_f')
        weather_hist_temp['sunset']= forecast.get('astro').get('sunset')
        weather_hist_temp['sunrise']= forecast.get('astro').get('sunrise')
        # weather_hist_list.append(weather_hist_temp)
        try:
            new = Weather_history(**weather_hist_temp)
            sess.add(new)
            sess.commit()
            # counter_all += 1

            return "successfully added to weather histrory"
        except:
            return "failed to add weather history"







def oura_sleep_call(new_token):

    url_sleep='https://api.ouraring.com/v1/sleep?start=2020-03-11&end=2020-03-21?'
    response_sleep = requests.get(url_sleep, headers={"Authorization": "Bearer " + new_token})
    sleep_dict = response_sleep.json()
    print('response_code: ',response_sleep.status_code)
    if response_sleep.status_code !=200:
        print('*** Error With Token ****')
        return 'Error with Token'
    else:
        return sleep_dict

def oura_sleep_db_add(sleep_dict, oura_token_id):
    # Add oura dictionary response to database
    startTime_db_oura_add = time.time()
    deleted_elements = 0 
    
    for sleep_session in sleep_dict['sleep']:
        sleep_session_exists = sess.query(Oura_sleep_descriptions).filter_by(
            bedtime_end = sleep_session.get('bedtime_end'),
            user_id = current_user.id).first()
        if not sleep_session_exists:

            # delete any dict element whose key is not in column list
            for element in list(sleep_session.keys()):
                if element not in Oura_sleep_descriptions.__table__.columns.keys():
                    # print('element to delete: ', element)
                    
                    del sleep_session[element]
                    deleted_elements += 1

            sleep_session['user_id'] = current_user.id
            sleep_session['token_id'] = oura_token_id
            #check if existing sleep bedtime_end exists if yes skip
            existing_sleep_bedtime_end = sess.query(Oura_sleep_descriptions).filter_by(
                user_id = current_user.id,
                bedtime_end = sleep_session['bedtime_end']
            ).first()
            if not existing_sleep_bedtime_end:
                new_sleep = Oura_sleep_descriptions(**sleep_session)
                sess.add(new_sleep)
                sess.commit()
    
    executionTime = (time.time() - startTime_db_oura_add)
    print('Add Oura Data Execution time in seconds: ' + str(executionTime))
    print(f'Number of eleements deleted {deleted_elements}')


def location_exists(user):
    
    min_loc_distance_difference = 1000

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

    if min_loc_distance_difference > .1:
        location_id = 0
    
    # returns location_id = 0 if there is no location less than sum of .1 degrees
    return location_id

