from flask import Blueprint
from flask import render_template, url_for, redirect, flash, request, abort, session,\
    Response, current_app, send_from_directory
# import bcrypt
from wsh_models import sess, Users, login_manager
from flask_login import login_required, login_user, logout_user, current_user




dash = Blueprint('dash', __name__)

@dash.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    print('Current User: ', current_user)
    print(dir(current_user))
    page_name = 'Dashboard'
    if request.method == 'POST':
        formDict = request.form.to_dict()
        # if formDict.get('login'):
        #     return redirect(url_for('users.login'))
        # elif formDict.get('register'):
        #     return redirect(url_for('users.register'))
        print('formDict::', formDict)
    return render_template('dashboard.html', page_name=page_name)