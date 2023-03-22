from flask import (Blueprint, render_template,request,redirect,url_for,session,flash)
from flask_login import login_required, current_user
from twilio.twiml import re
from twilio.twiml.messaging_response import MessagingResponse
from werkzeug.security import (check_password_hash, generate_password_hash)
from datetime import datetime, timedelta
from .utils import *
from .models import User,Settings,Idea
import json
import random

tz = timezone(timedelta(hours=2))


routes = Blueprint('routes',__name__,template_folder='templates')

@routes.route("/<item_pk>", methods=['POST','GET'])
@routes.route("/", methods=['POST','GET'])
def home(item_pk=None):

    user = session.get('user',default={})
    # Left this here for reference for future migrations
    #ideas = Idea.find().all()
    #for i in ideas:
    #    i_dict = i.dict()
    #    if not hasattr(i_dict,'time'):
    #        i.time = int(round(datetime.now().timestamp()))
    #        i.save()


    if request.method == 'POST':
        handle_request_form(request.form, user['pk'],item_pk)
        return redirect(url_for('routes.home'))



    if user:
        reminders, ideas, notebags = get_user_data(user['pk'])
    else:
        reminders = []
        ideas = []
        notebags = []


        

    return render_template('home.html',
                           session=session,
                           user=user,
                           reminders=reminders,
                           ideas=ideas,
                           notebags=notebags
                           )

    
@routes.route("/settings",methods=['POST','GET'])
def settings():
    user = session.get('user',default={})
    if not user:
        flash('login required')
        return redirect(url_for('routes.home'))

    

    print("User settings",user['settings'])
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
        elif "idea-stream" in request.form:
            ans = request.form.get('idea-stream')
            if user['settings']['idea_stream_public'] == "true":
                user['settings']['idea_stream_public'] = "false" 
                u = User.find(User.pk == user['pk']).first()
                u.settings.idea_stream_public = "false"
                u.save()
                flash('Ideas are now private')
                return redirect(url_for('routes.settings'))
            else:
                user['settings']['idea_stream_public'] = "true"
                u = User.find(User.pk == user['pk']).first()
                u.settings.idea_stream_public = "true"
                u.save()
                flash('Ideas are now public')
                return redirect(url_for('routes.settings'))
        
    
    return render_template('settings.html',
                           user=user
                           )


# -------------------------- EDITING/SAVING --------------------------
# --------------------------------------------------------------------

@routes.route("/move-<note_pk>-to-<bag_name>",methods=['POST','GET'])
def move_to(note_pk,bag_name):
    flash("here")
    user = session.get('user',default={})
    if not user:
        flash('login required')
        return redirect(url_for('routes.home'))
      
    if move_note(user['pk'],note_pk,bag_name):
        flash("note moved")
    else:
        flash("error moving the note")
    return redirect(url_for('routes.home'))


@routes.route("/note-to-<bag_name>",methods=['POST'])
def save_note_to_bag(bag_name):
    user = session.get('user',default={})
    if not user:
        flash('login required')
        return redirect(url_for('routes.home'))

    message = request.form.get('note')
    if message:
        if save_note(user['pk'], bag_name, message):
            flash("note saved!")
        else:
            flash("error saving the note")
    else:
        flash("note can't be empty")
    return redirect(url_for('routes.home'))
 

@routes.route("/edit-idea-<pk>", methods=['POST','GET'])
def edit_idea(pk):
    user = session.get('user',default=dict())
    if not user:
        flash('login required')
        return redirect(url_for('routes.home'))

    idea = Idea.find(Idea.pk == pk).first()
    cur_idea = idea.dict()
    if request.method == 'POST':
        new_idea = request.form.get('idea')
        if new_idea == "":
            Idea.delete(pk)
            flash("Idea deleted")
        else:
            idea.message = new_idea
            idea.save()
            flash("Idea edited")
        return redirect(url_for('routes.home'))

    return render_template('edit_idea.html',
                           user=user,
                           cur_idea=cur_idea)


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
                                       user=user,
                                       message=rem_message_str,
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
                return redirect(url_for('routes.home'))
            else: 
                reminder.message = msg
                reminder.save()
                flash("Message changed")
        
    return render_template('edit_reminder.html',
                           user=user,
                           message=rem_message_str,
                           reminder_pk=pk,
                           reocc=reminder.reoccurring,
                           method=reminder.remind_method
                           )

# -------------------------------------------------------------------------
#                                 DELETING 
# -------------------------------------------------------------------------

@routes.route("/delete-item/<item_type>/<item_pk>")
def delete_item(item_type, item_pk):
    user = session.get('user',default={})
    if not user:
        flash("Login required")
        return redirect(url_for('routes.home'))
    if item_type == "idea":
        Idea.delete(item_pk)
        flash("Idea deleted")
    elif item_type == "reminder":
        Reminder.delete(item_pk)
        flash("Reminder deleted")
    elif item_type == "note":
        if delete_note(user['pk'],item_pk):
            flash("Note deleted")
        else:
            flash("couldn't delete note")
    elif item_type == "notebag":
        if delete_notebag(user['pk'],item_pk):
            flash("Notebag deleted")
        else:
            flash("Couldn't delete notebag")

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
    
    if body.startswith("h"):
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
    elif body.startswith("all r"):
        all_reminders = user_all_reminders(str(user.pk))
        if not all_reminders:
            message = "No reminders."
        else:
            for r in all_reminders:
                message += str(r['time']) + " " + r['message'] + "\n"
    elif body.startswith("all i with"):
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

    elif body.startswith("r "):
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
    elif body.startswith("i "):
        if save_idea(str(user.pk),body[2:]):
            message = "Idea saved"
        else:
            message = "Error. Could not save the idea"

    elif body.startswith("t "):
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
    elif body.startswith("n "):
        # interface for adding notes
        if len(body) > 3:
            if save_note(user.pk,"main",body[2:]):
                message = "Note saved."
            else:
                message = "Error. Couldn't save the note"

    else:
        message = 'Wrong keyword. Type "h" for help.'

    resp = MessagingResponse()

    resp.message(message)
    return str(resp)


@routes.route("/<username>-ideas",methods=['POST','GET'])
def idea_stream(username):
    
    try:
        user = User.find(User.username == username).first()
    except NotFoundError:
        return 'no user found'
    if user.settings.idea_stream_public == "false":
        return "user's idea stream is off"
    ideas = user_all_ideas(user.pk)
    return render_template('idea_stream.html',username=username,ideas=ideas)


