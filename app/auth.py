from flask import (Blueprint, render_template,request,flash,url_for,redirect,session)
from flask import current_app as app
from werkzeug.security import (check_password_hash, generate_password_hash)
from redis_om.model.token_escaper import re
from .models import User
from . import config
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
        try:
            user = User.find(User.username == username).first()
        except:
            flash("No username found! Maybe signup?")
            return redirect(url_for('auth.login'))
        
        if not user:
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
        #user = User.find(User.username == username).first()
        #if user:
        #    flash("Username taken already! :/")
        #    return redirect(url_for('auth.signup'))
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


