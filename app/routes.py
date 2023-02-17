from flask import Blueprint, render_template,request,redirect,url_for,session
from flask_login import login_required, current_user
from twilio.twiml.messaging_response import MessagingResponse
from twilio.twiml.voice_response import VoiceResponse
from . import twilio_client,celery_app,tz
from datetime import datetime, timedelta
from .messaging import *
import json


routes = Blueprint('routes',__name__,template_folder='templates')

@routes.route("/", methods=['POST','GET'])
def home():


    logged_in = False
    if 'user' in session:
        if 'reminders' not in session:
            session['reminders'] = user_all_reminders()
        reminders = session.get('reminders') 
        logged_in = True
        print("hahah")
        user = session['user']
    else:
        user = dict()
        reminders = []

    if request.method == 'POST':
        if "test-data" in request.form:
            load_test_data()
        elif "all" in request.form:
            session['reminders'] = user_all_reminders()
        elif "this-minute" in request.form:
            session['reminders'] = all_reminders_this_minute()
        elif "delete-data" in request.form:
            delete_user_reminders()
        elif "call-me" in request.form:
            call(user['phone'])
        elif "text-me" in request.form:
            text(user['phone'],"hey there")
        else:
            msg = request.form['message']
            time_str = request.form['time']
            save_reminder(session['user']['pk'],msg,time_str)

        return redirect(url_for('routes.home'))
    print("LOG:",logged_in)

    return render_template('home.html',
                           user=user,
                           logged_in=logged_in,
                           reminders=reminders)

    
