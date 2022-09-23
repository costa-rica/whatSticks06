from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
# import bcrypt
from wsh_models import sess, Users, login_manager, User_location_day, Oura_sleep_descriptions
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime
import numpy as np
import pandas as pd
from app_package.dashboard.utilsChart import make_oura_df, make_user_loc_day_df, \
    make_weather_hist_df, df_for_nick, make_chart 



dash = Blueprint('dash', __name__)

@dash.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    print('current_User: ', current_user.email)
    page_name = 'Dashboard'

    any_loc_hist = sess.query(User_location_day).filter_by(user_id=current_user.id).all()
    any_oura_hist = sess.query(Oura_sleep_descriptions).filter_by(user_id=current_user.id).all()


    if current_user.id in [1, 2]:#If nick or guest use 
        df = df_for_nick()
        print('*** Acceing for Nick Data ****')

        temp_data_list = [round(int(temp)) for temp in df['avgtemp_f'].to_list() ]
        sleep_data_list = df['score'].to_list()
        dates_list =[datetime.strptime(i,'%Y-%m-%d') for i in df['date'].to_list() ]

        lists_tuple = (dates_list, sleep_data_list, temp_data_list)

        #calculate correlation:
        correlation = df['avgtemp_f'].corr(df['score'])
        #make chart
        script_b, div_b, cdn_js_b = make_chart(lists_tuple)
        return render_template('dashboard.html', page_name=page_name,
            script_b = script_b, div_b = div_b, cdn_js_b = cdn_js_b, 
            correlation = round(correlation, 2))

    elif len(any_loc_hist) > 0 or len(any_oura_hist) > 0:
        print('*** Acceing for Strnagers Data ****')
        df_oura_scores = make_oura_df()
        if df_oura_scores is None:
            df_oura_scores = []

        df_loc_da = make_user_loc_day_df()
        if df_loc_da is None:
            df_loc_da = []

        df_weath_hist = make_weather_hist_df()
        if df_weath_hist is None:
            df_weath_hist = []


        
        # Make weather history for only days the user has locations i.e. match on date and loc_id based on df_loc_day
        df_user_date_temp = pd.merge(df_loc_da, df_weath_hist, 
            how='left', left_on=['date', 'location_id'], right_on=['date', 'location_id'])
        df_user_date_temp = df_user_date_temp[df_user_date_temp['avgtemp_f'].notna()]

        print('---> THIS NEEDS TO be more than 0:::::: ', len(df_user_date_temp) )
        # print(df_user_date_temp)
        # print(df_oura_scores)



        if len(df_oura_scores) > 0 and len(df_user_date_temp) > 0:
        # if df_oura_scores is not None and df_user_date_temp is not None:
            print('-----> User has both oura and locaiton data')

            #TODO: This needs to concatenate
            # df = pd.merge(df_oura_scores, df_user_date_temp, how='left', left_on=['date'], right_on=['date'])
            # Combine our and temperatures to one df:
            df_oura_scores = df_oura_scores.set_index('date')
            df_user_date_temp = df_user_date_temp.set_index('date')
            df = pd.concat([df_user_date_temp, df_oura_scores], axis = 1)
            df.drop('id', inplace = True, axis = 1)
            df = df.where(pd.notnull(df), -99)
            df.reset_index(inplace = True)
            # print(df)
            
            # temp_data_list = [round(int(temp)) if temp!=-99 else None for temp in df['avgtemp_f'].to_list() ]
            temp_data_list = [round(int(temp)) for temp in df['avgtemp_f'].to_list() ]
            sleep_data_list = df['score'].to_list()
            dates_list =[datetime.strptime(i,'%Y-%m-%d') for i in df['date'].to_list() ]

            lists_tuple = (dates_list, sleep_data_list, temp_data_list)


            # resize df to remove empty avg temperature calculate correlation:
            df = df[df['avgtemp_f']!=-99]       

            if len(df) > 1:
                print('--- Has enough observations for correlations ----')
                correlation = round(df['avgtemp_f'].corr(df['score']),2)
            else:
                print('--- Has DOES NOT enough observations for correlations ----')
                correlation = 'too small sample'


            #make chart
            script_b, div_b, cdn_js_b = make_chart(lists_tuple)
            return render_template('dashboard.html', page_name=page_name,
                script_b = script_b, div_b = div_b, cdn_js_b = cdn_js_b, 
                correlation = correlation)

        #If user has 
        elif len(df_oura_scores) > 0:
            print('-----> User has only oura data')
        # elif df_oura_scores is not None:
            df = df_oura_scores.copy()
            dates_list =[datetime.strptime(i,'%Y-%m-%d') for i in df['date'].to_list() ]
            sleep_data_list = df['score'].to_list()
            temp_data_list = 'is empty'
            # lists_tuple = (dates_list, sleep_data_list, temp_data_list)
            
        elif len(df_user_date_temp) > 0:
            print('-----> User has only locaiton data')
        # elif df_user_date_temp is not None:
            df = df_user_date_temp.copy()
            dates_list =[datetime.strptime(i,'%Y-%m-%d') for i in df['date'].to_list() ]
            temp_data_list = [round(int(temp)) for temp in df['avgtemp_f'].to_list() ]
            sleep_data_list = 'is empty'
            
        lists_tuple = (dates_list, sleep_data_list, temp_data_list)


        #Use list data to make chart
        script_b, div_b, cdn_js_b = make_chart(lists_tuple)

        # print(div_b)

        return render_template('dashboard.html', page_name=page_name,
            script_b = script_b, div_b = div_b, cdn_js_b = cdn_js_b)
    else:
        df = ''

        return render_template('dashboard_empty.html', page_name=page_name)