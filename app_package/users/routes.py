from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
import bcrypt
from wsh_models import sess, Users, login_manager, Oura_token, Locations
from flask_login import login_required, login_user, logout_user, current_user


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

    if current_user.oura_token_id:
        oura_token = current_user.oura_token_id[0].token
    else:
        oura_token = ''

    if request.method == 'POST':
        formDict = request.form.to_dict()
        print('formDict:::', formDict)

        if formDict.get('oura_token'):
            #check if token exists for user
            if current_user.oura_token_id:
                print('* TOKEN found *')
                print('current_user.oura_token_id:', current_user.oura_token_id)
                current_user.oura_token_id[0].token = formDict.get('oura_token')
                sess.commit()

            #if token doesn't exist
            else:
                print('* No TOKEN found *')
                new_oura_token = Oura_token(
                                    id = current_user.id,
                                    token = formDict.get('oura_token'),
                                    )
                sess.add(new_oura_token)
                sess.commit()
            return redirect(url_for('users.account'))
        
        if formDict.get('location_text'):

            current_user.lat = formDict.get('location_text').split(',')[0]
            current_user.lon = formDict.get('location_text').split(',')[1]
            sess.commit()
    
    return render_template('account.html', page_name = page_name, email=email,
         oura_token = oura_token)