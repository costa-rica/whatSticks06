from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
# import bcrypt
from wsh_models import sess, Users, login_manager, User_location_day
from flask_login import login_required, login_user, logout_user, current_user
from datetime import datetime
import numpy
import pandas as pd
from app_package.dashboard.utilsChart import make_chart 



dash = Blueprint('dash', __name__)

@dash.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    print('Current User: ', current_user)
    print(dir(current_user))
    page_name = 'Dashboard'

    base_query = sess.query(User_location_day).filter_by(user_id = 1)

    current_user_id = current_user.id if current_user.id != 2 else 1
    df = pd.read_sql(str(base_query)[:-1] + str(current_user_id), sess.bind)
    print('df is what::: ', df)
    if df.empty:
        print('**** Yes that is what is its! ****')
        return render_template('dashboard_empty.html', page_name=page_name)
    else:
        print(' Data frame is not empyt')

    table_name = 'user_location_day_'
    cols = list(df.columns)
    for col in cols: df = df.rename(columns=({col: col[len(table_name):]}))
    
    #get rid of rows with missing temperature
    df = df[df['avgtemp_f'].notna()]

    #Make list date
    # temp_data_list = [round(int(temp)) if temp!=None else 1000 for temp in df['avgtemp_f'].to_list() ]
    temp_data_list = [round(int(temp)) for temp in df['avgtemp_f'].to_list() ]

    sleep_data_list = df['score'].to_list()

    dates_list =[datetime.strptime(i,'%Y-%m-%d') for i in df['date'].to_list() ]

    script_b, div_b, cdn_js_b = make_chart(dates_list, temp_data_list, sleep_data_list)

    #calculate correlation:
    correlation = df['avgtemp_f'].corr(df['score'])


    if request.method == 'POST':
        formDict = request.form.to_dict()

        print('formDict::', formDict)

    return render_template('dashboard.html', page_name=page_name,
        script_b = script_b, div_b = div_b, cdn_js_b = cdn_js_b, 
        correlation = round(correlation, 2))