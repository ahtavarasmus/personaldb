from flask import (Blueprint, render_template,request,flash,url_for,redirect,session)
from flask import current_app as app
from werkzeug.security import (check_password_hash, generate_password_hash)
from redis_om.model.token_escaper import re
from .models import User
from . import config
from .messaging import *
import random,time

auth = Blueprint('auth',__name__,template_folder='templates')


@auth.route("/login", methods=['POST','GET'])
def login():
    user = session.get('user',default={})

    if user:
        return redirect(url_for('routes.home'))

    if request.method == 'POST':
        if "forgot" in request.form:
            return redirect(url_for('auth.forgot'))
        username = request.form.get('username')
        password = request.form.get('password')
        # following is really bad i know, idk how 
        try:
            user = User.find(User.username == username).first()
            if not user:
                flash("No username found! Maybe signup?")
                return redirect(url_for('auth.login'))
        except:
            flash("No username found! Maybe signup?")
            return redirect(url_for('auth.login'))
        
        user = user.dict()
        if check_password_hash(str(user['password']),str(password)):
            session['user'] = user
            return redirect(url_for('routes.home'))
        flash("Wrong password!")

        return redirect(url_for('auth.login'))

    return render_template('login.html')


@auth.route("/signup",methods=['POST','GET'])
def signup():

    user = session.get('user',default={})

    if user:
        return redirect(url_for('routes.home'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        phone = request.form.get('phone')
        # how do i do the following?
        try:
            user_exists = User.find(User.username == username).first()
            if user_exists:
                flash("Username taken already! :/")
                return redirect(url_for('auth.signup'))
        except:
            flash("Username taken already! :/")
            return redirect(url_for('auth.signup'))
        user = User(username=username,password=generate_password_hash(password, method='sha256'),phone=phone,ideas=[])
        user.save()
        user = user.dict()
        session['user'] = user 
        return redirect(url_for('routes.home'))

    return render_template('signup.html')

@auth.route("/logout", methods=['GET','POST'])
def logout():
    if 'user' in session:
        flash('Logged out!')
        session.pop('user')
    return redirect(url_for('auth.login'))

@auth.route("/token", methods=['POST','GET'])
def token():

    user = session.get('user',default=dict())

    todo = session.get("todo", default="")
 
    if todo == "change_phone":
        to = user['phone']
    elif todo == "forgot_password":
        to = session.get('phone')
    else:
        # this won't happen
        return redirect(url_for('routes.home'))

    if request.method == 'POST':
        if "resend" in request.form:
            send_code(to)
            return render_template('token.html')
        post_code = request.form.get('code')
        hash_code = session.get('code',default="")
        if (check_password_hash(hash_code,str(post_code))):
            if todo == "change_phone":
                new_phone = session.get('phone')
                print(user['pk'])
                usr = User.find(User.pk == user['pk']).first()
                usr.phone = session.get('phone')
                usr.save()
                user['phone'] = session.get('phone')
                session.pop('phone')
                session.pop('code')
                session.pop("todo")
                flash("Number changed!")
                return redirect(url_for('routes.settings'))
            elif todo == "forgot_password":
                to = session.get('phone')
                session.pop('phone')
                session.pop("todo")
                session.pop("code")
                user = User.find(User.phone == to).first().dict()
                session['user'] = user
                flash("Logged in. Now go change your password.")
                return redirect(url_for('routes.settings'))
        else:
            flash("Wrong code!")
            return redirect(url_for('auth.token'))
    send_code(to)
    return render_template('token.html')

@auth.route("/forgot", methods=['POST','GET'])
def forgot():
    if request.method == 'POST':
        username = request.form.get('username')
        try:
            user = User.find(User.username == username).first()
            if not user:
                flash("No username found! Maybe signup?")
                return redirect(url_for('auth.forgot'))
        except:
            flash("No username found! Maybe signup?")
            return redirect(url_for('auth.forgot'))
        user_dict = user.dict()
        session['phone'] = user_dict['phone']
        session['todo'] = "forgot_password"
        return redirect(url_for('auth.token'))

        

    return render_template('forgot.html')
