from types import MethodDescriptorType
from flask import Blueprint, render_template,request,redirect,url_for,session,flash
from flask_login import login_required, current_user
from twilio.twiml import re
from twilio.twiml.messaging_response import MessagingResponse
from werkzeug.security import (check_password_hash, generate_password_hash)
from twilio.twiml.voice_response import VoiceResponse
from datetime import datetime, timedelta
from .messaging import *
from .saving_querying import (user_all_reminders,all_reminders_this_minute,
save_idea,user_all_ideas,stop_timer,start_timer,all_timers)
from .utils import format_ideas
import json
import random

tz = timezone(timedelta(hours=2))

routes = Blueprint('routes',__name__,template_folder='templates')

@routes.route("/", methods=['POST','GET'])
def home():

    user = session.get('user',default={})

    if request.method == 'POST':
        if "test-data" in request.form:
            load_test_data()
        elif "all" in request.form:
            session['reminders'] = user_all_reminders(user['pk'])
        elif "this-minute" in request.form:
            session['reminders'] = all_reminders_this_minute()
        elif "reminder" in request.form:
            msg = request.form['message']
            time_str = request.form['time']
            save_reminder(session['user']['pk'],msg,time_str)
        elif "idea" in request.form:
            msg = request.form['message']
            save_idea(session['user']['pk'],msg)
        
        return redirect(url_for('routes.home'))



    if user:
        reminders = session.get(
            'reminders',default=user_all_reminders(user['pk']))
        ideas = user_all_ideas(user['pk'])
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
        if "new_phone" in request.form:
            new_phone = request.form.get('new_phone')
            session['phone'] = new_phone
            session['todo'] = "change_phone"
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

@routes.route("/sms-webhook",methods=['POST'])
def sms_webhook():

    phone = request.values.get('From',None)
    body = request.values.get('Body',None)
    if body == None or phone == None: 
        print("NO MESSAGE OR PHONE")
        return "no message or phone",404
    try:
        user = User.find(User.phone == phone).first()
    except:
        print("USER NOT FOUND")
        return "user not found",404
    message = ""
    
    if body[0] == "h":
        if body[2] == "r":
            message = '''"r [body]" -> add reminder,
                        [body] must include a message and date 
                        formatted like "12/2/2054 23:00" somewhere.
                        e.g. "r groceries 12/2/2054 12:00".
                        
                        "all r" -> get all reminders.
            '''
        if body[2] == "i":
            message = '''"i [body]" -> add idea,
                        [body] has the idea.
                        e.g. "i bake more" adds a "bake more" idea.

                        "all i with [body]" -> get all ideas, 
                        that have the keyword [body].
                        E.g. "all i with bake" returns every idea 
                        where you used the word "bake".
            '''
        if body[2] == "t":
            message = '''"t [body]" -> adds a new timer,
                        [body] must include a minute value.
                        E.g. "t 20min" will add timer for 20 minutes.

                        "t stop" -> stops the current timer.
            '''
        else:
            message = '''
                    "r [body]"->add reminder
                    "all r"   ->get all reminders
                    "i [body]"->save idea
                    "all i with [body]" -> all ideas with [body]
                    "t [body]"->start timer
                    "t stop"  ->stop timer

                    Use "h [x]" to get more info about x->(r,i or t).

                      
                    "
                    '''
    elif body[:5] == "all r":
        all_reminders = user_all_reminders(str(user.pk))
        if not all_reminders:
            message = "No reminders."
        else:
            for r in all_reminders:
                message += str(r['time']) + " " + r['message'] + "\n"
    elif body[:10] == "all i with":
        key = body[11:]
        user_pk = str(user.pk)
        ideas_obj = Idea.find((Idea.user == user_pk) and 
                          (Idea.message % key)).all()
        ideas = format_ideas(ideas_obj)
        if not ideas:
            message = "No ideas found."
        else:
            for i in ideas:
                message += "- "+i['message']+"\n"

    elif body[:2] == 'r ':
        t = re.search(r"\d+\/\d+\/\d+",body[2:])
        t2 = re.search(r"\d+\:\d+",body[2:])
        if t == None or t2 == None:
            message = 'Error. Date format not right. See-> '
        else:
            time = t.group() + " " + t2.group()
            msg = ""
            first_add = True
            for x in body[2:].split():
                if x != t.group() and x != t2.group():
                    if first_add:
                        msg += x
                        first_add = False
                    else:
                        msg += " "+x
            if save_reminder(str(user.pk),msg,time):
                message = "Reminder saved."
            else:
                message = "Error. Could not save the reminder"
    elif body[:2] == 'i ':
        if save_idea(str(user.pk),body[2:]):
            message = "Idea saved"
        else:
            message = "Error. Could not save the idea"

    elif body[:2] == 't ':
        found = re.search("\d+",body[2:])
        stop = re.search("stop",body[2:])
        if stop != None:
            stop_timer(str(user.pk))
            message = "Timer stopped"
        else:  
            if found == None:
                message = "Error. Either give time in minutes or write stop"
            else:
                minutes = int(found.group())
                if start_timer(str(user.pk),minutes):
                    message = f"Timer for {minutes}min started"
                else:
                    message = f'Error. Another timer already going. Use "t stop" to stop it'
    else:
        message = 'Wrong keyword. Type "h" for help.'

    resp = MessagingResponse()

    resp.message(message)
    return str(resp)
