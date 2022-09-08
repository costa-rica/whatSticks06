from flask_login import login_required, login_user, logout_user, current_user
import json
import requests
from datetime import datetime
from wsh_models import sess, Users, Locations, Weather_history, Oura_token, Oura_sleep_descriptions


def oura_sleep_call(new_token):
    print('*********')
    print('** Made Oura Ring Call ***')
    print('******')
    url_sleep='https://api.ouraring.com/v1/sleep?start=2020-03-11&end=2020-03-21?'
    response_sleep = requests.get(url_sleep, headers={"Authorization": "Bearer " + new_token})
    print('status_code: ', response_sleep.status_code)
    sleep_dict = response_sleep.json()
    print('len of response: ', len(sleep_dict))
    return sleep_dict

def oura_sleep_db_add(sleep_dict, oura_token_id):
    # Add oura dictionary response to database
    
    for sleep_session in sleep_dict['sleep']:
        sleep_session_exists = sess.query(Oura_sleep_descriptions).filter_by(
            bedtime_end = sleep_session.get('bedtime_end'),
            user_id = current_user.id).first()
        if not sleep_session_exists:
            print('Keys in first sleep session: ', sleep_session.keys())
            print('There are ', len(sleep_session.keys()), ' keys in this list')

# delete any dict element whose key is not in column list
            for element in list(sleep_session.keys()):
                if element not in Oura_sleep_descriptions.__table__.columns.keys():
                    print('element to delete: ', element)
                    
                    del sleep_session[element]


            # if sleep_session.get('hr_5min'):
            #     del sleep_session['hr_5min']
            #     del sleep_session['hypnogram_5min']
            #     del sleep_session['rmssd_5min']
            # if sleep_session.get('temperature_trend_deviation') or sleep_session.get('temperature_trend_deviation') ==0:
            #     print('**** does this get fired ****')
            #     del sleep_session['temperature_trend_deviation']
            # if sleep_session.get('timestamp'):
            #     del sleep_session['timestamp']
            print('*** After Deleteion ***')
            
            print('There are ', len(sleep_session.keys()), ' keys in this list')
            print(sleep_session.keys())
            sleep_session['user_id'] = current_user.id
            sleep_session['token_id'] = oura_token_id
            new_sleep = Oura_sleep_descriptions(**sleep_session)
            sess.add(new_sleep)
            sess.commit()