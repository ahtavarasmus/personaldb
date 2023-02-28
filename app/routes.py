from types import MethodDescriptorType
from flask import Blueprint, render_template,request,redirect,url_for,session,flash
from flask_login import login_required, current_user
from twilio.twiml import re
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
@routes.route("/edit-idea-<idea>", methods=['POST','GET'])
def edit_idea(idea):
    user = session.get('user',default=dict())
    if not user:
        flash('login required')
        return redirect(url_for('routes.home'))

    user_obj = User.find(User.pk == user['pk']).first()
    if request.method == 'POST':
        new_idea = request.form.get('idea')
        if new_idea == "":
            user_obj.ideas.remove(idea)
            flash("Idea deleted")
        else:
            user_obj.ideas[user_obj.index(idea)] = new_idea 
            flash("Idea edited")
        user_obj.save()
        return redirect(url_for('routes.home'))

    return render_template('edit_idea.html',
                           cur_idea=idea)


@routes.route("/edit-reminder-<pk>", methods=['POST','GET'])
def edit_reminder(pk):
    user = session.get('user',default=dict())
    if not user:
        flash("login required")
        return redirect(url_for('routes.home'))

    try: 
        reminder = Reminder.find(Reminder.pk == pk).first()
    except NotFoundError:
        flash("reminder not found")
        return redirect(url_for('routes.home'))

    rem_message_str = reminder.dict()['message']

    if request.method == 'POST':
        if 'time' in request.form:
            time = request.form.get('time')
            try:
                time_obj = datetime.strptime(str(time),
                    "%d/%m/%y %H:%M").replace(tzinfo=tz)
            except ValueError as e:
                print(e)
                flash("Date format not right")
                return render_template('edit_reminder.html',
                                       reminder_pk=pk)
            epoch_time = int(round(time_obj.timestamp()))
            reminder.time = epoch_time
            reminder.save()
            flash("Time changed")
        elif 'msg' in request.form:
            msg = request.form.get('msg')
            if msg == "":
                Reminder.delete(pk)
                flash("Reminder Deleted")
            else: 
                reminder.message = msg
                reminder.save()
                flash("Message changed")

        return redirect(url_for('routes.home'))
    return render_template('edit_reminder.html',
                            message=rem_message_str,
                           reminder_pk=pk
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
    flash("idea deleted")
    return redirect(url_for('routes.home'))
    
@routes.route("/delete-reminder-<pk>")
def delete_reminder(pk):

    user = session.get('user',default=dict())
    if not user:
        flash('login required')
        return redirect(url_for('routes.home'))
    Reminder.delete(pk)
    flash("reminder delete")
    return redirect(url_for('routes.home'))


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
    
    if body[:5] == "all r":
        all_reminders = user_all_reminders(str(user.pk))
        if not all_reminders:
            message = "no reminders"
        else:
            for r in all_reminders:
                message += str(r['time']) + " " + r['message'] + "\n"

    elif body[:2] == 'r ':
        t = re.search(r"\d+\/\d+\/\d+",body[2:])
        t2 = re.search(r"\d+\:\d+",body[2:])
        if t == None or t2 == None:
            message = "Date format not right"
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
                message = "Could not save the reminder"
    elif body[:2] == 'i ':
        if save_idea(str(user.pk),body[2:]):
            message = "Idea saved"
        else:
            message = "Could not save the idea"
    else:
        message = "wrong keyword"

    resp = MessagingResponse()

    resp.message(message)
    return str(resp)
