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

    if request.method == 'POST':
        if 'new_phone' in request.form:
            new_phone = request.form.get('new_phone')
            session['new_phone'] = new_phone
            token = random.randrange(10000,99999)
            hash_code = generate_password_hash(str(token))
            session['code'] = hash_code
            text(user['phone'],f"Code:\n {token}")
            flash("Code sent!")
            return redirect(url_for('auth.token'))
            
        else:
            post_code = request.form.get('code')
            hash_code = session.get('code',default="")
            if (check_password_hash(hash_code,str(post_code))):
                flash("Number changed!")
                usr = User.find(User.pk == user['pk']).first()
                usr.phone = session.get('new_phone')
                usr.save()
                user['phone'] = session.get('new_phone')
                session.pop('new_phone')
                session.pop('code')
                return redirect(url_for('routes.settings'))
            else:
                flash("Wrong code!")
                return redirect(url_for('auth.token'))
            
    return render_template('token.html')

