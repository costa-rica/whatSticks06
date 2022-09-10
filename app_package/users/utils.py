from flask import current_app
from flask_login import login_required, login_user, logout_user, \
    current_user
import json
import requests
from datetime import datetime
from wsh_models import sess, Users, Locations, Weather_history, \
    Oura_token, Oura_sleep_descriptions, User_location_day


def oura_sleep_call(new_token):
    # print('*********')
    # print('** Made Oura Ring Call ***')
    # print('******')
    url_sleep='https://api.ouraring.com/v1/sleep?start=2020-03-11&end=2020-03-21?'
    response_sleep = requests.get(url_sleep, headers={"Authorization": "Bearer " + new_token})
    # print('status_code: ', response_sleep.status_code)
    sleep_dict = response_sleep.json()
    # print('len of response: ', len(sleep_dict))
    if response_sleep.status_code !='200':
        print('*** Error With Token ****')
        return 'Error with Token'
    else:
        return sleep_dict

def oura_sleep_db_add(sleep_dict, oura_token_id):
    # Add oura dictionary response to database
    
    for sleep_session in sleep_dict['sleep']:
        sleep_session_exists = sess.query(Oura_sleep_descriptions).filter_by(
            bedtime_end = sleep_session.get('bedtime_end'),
            user_id = current_user.id).first()
        if not sleep_session_exists:
            # print('Keys in first sleep session: ', sleep_session.keys())
            # print('There are ', len(sleep_session.keys()), ' keys in this list')

            # delete any dict element whose key is not in column list
            for element in list(sleep_session.keys()):
                if element not in Oura_sleep_descriptions.__table__.columns.keys():
                    print('element to delete: ', element)
                    
                    del sleep_session[element]


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

def weather_api_call():
    print('***** weather_api_call Funct *****')
    #1) get weatehr api token form config
    api_token = [j  for i,j in current_app.config.items() if i=='WEATHER_API_KEY'][0]

    #2) get location from current user
    location_coords = f'{current_user.lat},{current_user.lon}'


    #3) make weather call 
    base_url = 'http://api.weatherapi.com/v1'
    # current = '/current.json'
    # astronomy = '/astronomy.json'
    history = '/history.json'

    payload = {}
    payload['q'] = location_coords
    payload['key'] = api_token

    payload['dt'] = datetime.today().strftime('%Y-%m-%d')
    # payload['end_dt'] = '2022-09-09'
    payload['hour'] = 0

    r_history = requests.get(base_url + history, params = payload)
    print('r_history status code: ', r_history.status_code)
    weather_dict = r_history.json()
    # print(payload)
    print('******')
    print('weather_api dict')
    print(weather_dict)
    #4) return dictionary
    return weather_dict

def add_db_locations(weather_dict):
    add_dict = {}
    add_dict['city'] = weather_dict.get('location').get('name')
    add_dict['region'] = weather_dict.get('location').get('region')
    add_dict['country'] = weather_dict.get('location').get('country')
    add_dict['lat'] = weather_dict.get('location').get('lat')
    add_dict['lon'] = weather_dict.get('location').get('lon')
    new = Locations(**add_dict)
    sess.add(new)
    sess.commit()
    return new.id

def add_db_weather_hist(weather_dict, location_id):
    hist_forecast_list = weather_dict.get('forecast').get('forecastday')
    
    weather_hist_list=[]
    for forecast in hist_forecast_list:
        weather_hist_temp ={}
        # Get location stuff

        weather_hist_temp['city_location_name'] = weather_dict.get('location').get('name')
        weather_hist_temp['region_name'] = weather_dict.get('location').get('region')
        weather_hist_temp['country_name'] = weather_dict.get('location').get('country')
        weather_hist_temp['lat'] = weather_dict.get('location').get('lat')
        weather_hist_temp['lon'] = weather_dict.get('location').get('lon')
        weather_hist_temp['tz_id'] = weather_dict.get('location').get('tz_id')
        weather_hist_temp['location_id'] = location_id #needs location id*****
        
        #Get temperature stuff
        weather_hist_temp['date']= forecast.get('date')
        weather_hist_temp['maxtemp_f']= forecast.get('day').get('maxtemp_f')
        weather_hist_temp['mintemp_f']= forecast.get('day').get('mintemp_f')
        weather_hist_temp['avgtemp_f']= forecast.get('day').get('avgtemp_f')
        weather_hist_temp['sunset']= forecast.get('astro').get('sunset')
        weather_hist_temp['sunrise']= forecast.get('astro').get('sunrise')
        weather_hist_list.append(weather_hist_temp)
        new = Weather_history(**weather_hist_list[0])
        sess.add(new)
        sess.commit()

        return new.id

def db_add_user_loc_day(avgtemp_f, location_id):
    print('***in db_add_user_loc_day ***')
    # print(weather_dict)
    #1) dict with stuff
    add_dict = {}
    #2) add these itmes
        #user_id
    add_dict['user_id'] = current_user.id
        

        #date
    add_dict['date'] = datetime.today().strftime('%Y-%m-%d')
        #local_time
    add_dict['local_time'] = datetime.now().strftime("%H:%M:%S")
        #avgtemp_f
    # add_dict['avgtemp_f'] = weather_dict.get('forecast').get('forecastday').get('day').get('avgtemp_f')
    add_dict['avgtemp_f'] = avgtemp_f
        #row_tpe = 'user'
    add_dict['row_type'] = 'user'
        #locagtion_id
    add_dict['location_id'] = location_id

    new = User_location_day(**add_dict)
    sess.add(new)
    sess.commit()

    return new.id

