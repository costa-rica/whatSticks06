from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, \
    abort, session, Response, current_app, send_from_directory
import bcrypt
from wsh_models import sess, Users, login_manager, Oura_token, Locations, \
    Weather_history
from flask_login import login_required, login_user, logout_user, current_user
import requests
from app_package.users.utils import oura_sleep_call, oura_sleep_db_add
from sqlalchemy import func

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
        
        if formDict.get('location_text'):

            current_user.lat = formDict.get('location_text').split(',')[0]
            current_user.lon = formDict.get('location_text').split(',')[1]
            sess.commit()

            
    
    return render_template('account.html', page_name = page_name, email=email,
         oura_token = oura_token)