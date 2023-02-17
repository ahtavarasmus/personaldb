from flask import (Blueprint, render_template,request,flash,url_for,redirect,session)
from flask import current_app as app
from werkzeug.security import (check_password_hash, generate_password_hash)
from redis_om.model.token_escaper import re
from .models import User
from . import (config,twilio_client)
import random,time

auth = Blueprint('auth',__name__,template_folder='templates')


@auth.route("/login", methods=['POST','GET'])
def login():
    logged_in = False
    if 'user' in session:
        logged_in = True
        return redirect(url_for('routes.home'))
    if request.method == 'POST':

        username = request.form.get('username')
        password = request.form.get('password')
        user = User.find(User.username == username).first()
        
        print(user)
        if not user:
            flash("No username found! Maybe signup?")
            return redirect(url_for('auth.login'))
        user = user.dict()
        print("pass:",user['password'])
        if check_password_hash(str(user['password']),str(password)):
            session['user'] = user
            return redirect(url_for('routes.home'))
        flash("Wrong password!")

        print("hahah")
        return redirect(url_for('auth.login'))

    return render_template('login.html',
                           logged_in=logged_in
                           )


@auth.route("/signup",methods=['POST','GET'])
def signup():
    logged_in = False
    if 'user' in session:
        logged_in = True
        return redirect(url_for('routes.home'))


    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        phone = request.form.get('phone')
        #user = User.find(User.username == username).first()
        #if user:
        ##    flash("Username taken already! :/")
        #    return redirect(url_for('auth.signup'))
        user = User(username=username,password=generate_password_hash(password, method='sha256'),phone=phone)
        user.save()
        user = user.dict()
        session['user'] = user
        return redirect(url_for('routes.home'))

    return render_template('signup.html',logged_in=logged_in)

@auth.route("/logout", methods=['GET','POST'])
def logout():
    if 'user' in session:
        flash('Logged out!')
        session.pop('user')
    return redirect(url_for('auth.login'))


