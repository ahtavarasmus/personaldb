from flask import Blueprint, render_template,request,redirect,url_for,session
from flask_login import login_required, current_user
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse
from . import celery_app,tz
from datetime import datetime, timedelta
from .messaging import *
import json


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
    else:
        reminders = []


        

    return render_template('home.html',
                           session=session,
                           user=user,
                           reminders=reminders)

    
@routes.route("/settings",methods=['POST','GET'])
def settings():
    user = session.get('user',default={})
    
    return render_template('settings.html',
                           user=user
                           )
