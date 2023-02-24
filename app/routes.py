from flask import Blueprint, render_template,request,redirect,url_for,session,flash
from flask_login import login_required, current_user
from twilio.twiml.messaging_response import MessagingResponse
from werkzeug.security import (check_password_hash, generate_password_hash)
from twilio.twiml.voice_response import VoiceResponse
from . import celery_app,tz
from datetime import datetime, timedelta
from .messaging import *
import json
import random


routes = Blueprint('routes',__name__,template_folder='templates')

@routes.route("/", methods=['POST','GET'])
def home():

    user = session.get('user',default={})

    if request.method == 'POST':
        if "test-data" in request.form:
            load_test_data()
        elif "all" in request.form:
            session['reminders'] = user_all_reminders()
        elif "this-minute" in request.form:
            session['reminders'] = all_reminders_this_minute()
        elif "delete-data" in request.form:
            print("HERE")
            delete_user_reminders()
        elif "call-me" in request.form:
            call(user['phone'])
        elif "text-me" in request.form:
            print("PHONE=",user['phone'])
            text(user['phone'],"hey there")
        elif "reminder" in request.form:
            msg = request.form['message']
            time_str = request.form['time']
            save_reminder(session['user']['pk'],msg,time_str)
        elif "idea" in request.form:
            msg = request.form['message']
            save_idea(session['user']['pk'],msg)


    if user:
        reminders = session.get(
            'reminders',default=user_all_reminders())
        ideas = user_all_ideas()
    else:
        reminders = []
        ideas = []


        

    return render_template('home.html',
                           session=session,
                           user=user,
                           reminders=reminders,
                           ideas=ideas
                           )

    
@routes.route("/settings",methods=['POST','GET'])
def settings():
    user = session.get('user',default={})
    if not user:
        flash('login required')
        return redirect(url_for('routes.home'))


    if request.method == 'POST':
        if "phone-change" in request.form:
            return redirect(url_for('auth.token'))

        elif "change-password" in request.form:
            new_pass = request.form.get('password')
            u = User.find(User.pk == user['pk']).first()
            u.password = generate_password_hash(str(new_pass),method='sha256')
            u.save()
            flash("Password changed!")
            return redirect(url_for('routes.settings'))
        
    
    return render_template('settings.html',
                           user=user
                           )
@routes.route("/delete-idea-<idea>")
def delete_idea(idea):
    user = session.get('user',default=dict())
    if not user:
        flash('login required')
        return redirect(url_for('routes.home'))
    user_obj = User.find(User.pk == user['pk']).first()
    user_obj.ideas.remove(idea)
    user_obj.save()
    user['ideas'].remove(idea)
    return redirect(url_for('routes.home'))

@routes.route("/edit-reminder-<pk>", methods=['POST','GET'])
def edit_reminder(pk):
    reminder = Reminder.find(Reminder.pk == pk).first().dict()
    user = session.get('user')
    if request.method == 'POST':
        if 'delete' in request.form:
            Reminder.delete(pk)
        elif 'time' in request.form:
            time = request.form.get('time')
            save_reminder(user['pk'],reminder['message'],time)
            Reminder.delete(pk)
        elif 'msg' in request.form:
            pass



