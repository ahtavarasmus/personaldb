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


    if current_user.is_authenticated:
        if 'reminders' not in session:
            session['reminders'] = user_all_reminders()
        reminders = session.get('reminders') 
    else:
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
            call(current_user['phone'])
        elif "text-me" in request.form:
            text(current_user['phone'],"hey there")
        else:
            msg = request.form['message']
            time_str = request.form['time']
            save_reminder(current_user['pk'],msg,time_str)

        return redirect(url_for('routes.home'))

    return render_template('home.html',
                           user=current_user,
                           reminders=reminders)

    
