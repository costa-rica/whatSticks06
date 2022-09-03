from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
import bcrypt
from wsh_models import sess, Users, login_manager
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
        if formDict.get('password'):
            if bcrypt.checkpw(formDict.get('password').encode(), user.password):
                print("match")
                login_user(user)
                flash('Logged in succesfully')
                # next = request.args.get('next')
                # if not is_safe_url(next):
                #     return flask.abort(400)
                return redirect(url_for('dash.dashboard'))
            else:
                print("does not match")

        # if successsful login_something_or_other...

        if formDict.get('page'):
            return redirect(url_for('users.page'))
        elif formDict.get('protected_page'):
            return redirect(url_for('users.protected_page'))
        elif formDict.get('logout'):
            return redirect(url_for('users.logout'))

        if current_user:
            print('current_user:::')
            print(dir(current_user))
    
    return render_template('login.html', page_name = page_name)

@users.route('/register', methods = ['GET', 'POST'])
def register():
    page_name = 'Register'
    if request.method == 'POST':
        formDict = request.form.to_dict()
        hash_pw = bcrypt.hashpw(formDict.get('password').encode(), salt)
        new_user = Users(email = formDict.get('email'), password = hash_pw)
        sess.add(new_user)
        sess.commit()
        return redirect(url_for('users.login'))

    return render_template('login.html', page_name = page_name)


@users.route('/protected_page', methods = ['GET', 'POST'])
@login_required
def protected_page():
    page_name = 'Protected Page'
    something = current_user
    if request.method == 'POST':
        formDict = request.form.to_dict()
        email = formDict.get('email')

        if formDict.get('page'):
            return redirect(url_for('users.page'))
        elif formDict.get('protected_page_1'):
            return redirect(url_for('users.protected_page'))
        elif formDict.get('logout'):
            return redirect(url_for('users.logout'))
    
    return render_template('protected_page.html', page_name = page_name,
        current_user = current_user)

@users.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('users.login'))