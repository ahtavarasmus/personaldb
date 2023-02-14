from flask import Blueprint, render_template,request,flash,url_for,redirect,session
from flask import current_app as app
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash
from redis_om.model.token_escaper import re
from .models import User
from . import login_manager,config,twilio_client
import random,time

auth = Blueprint('auth',__name__,template_folder='templates')


@auth.route("/login", methods=['POST','GET'])
def login():
    if request.method == 'POST':

        username = request.form.get('username')
        user = User.find(User.username == username).first().dict()

        if not user:
            flash("No username found! Maybe signup?")
            return redirect(url_for('auth.login'))

        phone = user['phone']
        token = random.randrange(10000, 99999) 

        session['user'] = user['username']
        session['token'] = generate_password_hash(str(token),method='sha256')

        twilio_client.messages.create(
                body=str(token),
                to=phone,
                messaging_service_sid=config.get('TWILIO_MSG_SID')
                )
        flash("Code sent!")
        return redirect(url_for('auth.token'))

    return render_template('login.html',user=current_user)


@auth.route("/token", methods=['GET','POST'])
def token_view():
    if request.method == 'POST':
        user_token = request.form.get('token')
        token = session.get('token')
        if token and user_token and check_password_hash(token,user_token):
            user = User.find(session.get('user')).first()
            login_user(user.dict(),remember=True)
            return redirect(url_for('routes.home'))
        else:
            flash("Error! Pls try again:)")
            return redirect(url_for('auth.login'))
    return render_template('token.html')



@auth.route("/signup",methods=['POST','GET'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        phone = request.form.get('phone')
        user = User.find(User.username == username).first().dict()
        if user:
            flash("Username taken already! :/")
            return redirect(url_for('auth.signup'))
        user = User(username=username,phone=phone)
        user.save()
        login_user(user.dict(),remember=True)
        return redirect(url_for('routes.home'))

    return render_template('signup.html',user=current_user)


@login_manager.user_loader
def load_user(user_pk):
    if user_pk is not None:
        return User.find(User.pk == user_pk).first().dict()
    return None

@login_manager.unauthorized_handler
def unauthorized():
    flash("You need to login first to see this page.")
    return redirect(url_for('auth.login'))


