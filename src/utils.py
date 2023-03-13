# External
from flask import session,flash
from twilio.rest import Client
from redis_om import NotFoundError
from werkzeug.security import (check_password_hash, generate_password_hash)
from operator import itemgetter
import json
import random

# Internal
from .models import Reminder,User,Idea,Timer,Note,NoteBag
from datetime import datetime, time,timedelta,timezone

# specific config
tz = timezone(timedelta(hours=2))

with open('/etc/personaldb_config.json') as config_file:
    config = json.load(config_file)

client = Client(config.get('TWILIO_ACCOUNT_SID'),
                    config.get('TWILIO_AUTH_TOKEN'))

# Fiel Order:
# Utility
# Saving
# Deleting
# Querying
# Sending
# Testing

# ----------------------- UTILITY ----------------------------------------
#-------------------------------------------------------------------------

def format_ideas(ideas):
    """
    Receives a list of idea json objects
    and turns them into list of dicts
    """
    response = []
    for idea in ideas:
        i_dict = idea.dict()
        i_dict['time'] = datetime.fromtimestamp(i_dict['time'])
        response.append(i_dict)
    response = sorted(response, key=itemgetter('time'), reverse=True)
    return response

def format_reminders(reminders):
    """ 
    Receives a list of reminder json objects
    and turns them into list of dicts 
    """
    response = []
    for reminder in reminders:
        rem_dict = reminder.dict()
        rem_dict['time'] = datetime.fromtimestamp(rem_dict['time'])
        response.append(rem_dict)

    response = sorted(response, key=itemgetter('time'), reverse=True)
    return response

def format_timers(timers):
    
    response = []
    for timer in timers:
        timer_dict = timer.dict()

        timer_dict['time'] = datetime.fromtimestamp(timer_dict['time'])
        response.append(timer_dict)

    return response


# --------------- SAVING -------------------------------------------------
#-------------------------------------------------------------------------
def save_reminder(user_pk,msg,time_str):
    """
    saves a reminder to redis
    return: True if success, else False
    """
    try:
        time_obj = datetime.strptime(str(time_str), "%d/%m/%y %H:%M").replace(tzinfo=tz)
    except ValueError:
        return False
    epoch_time = int(round(time_obj.timestamp()))
    new_reminder = Reminder(user=user_pk,
                            message=msg,
                            time=epoch_time
                            )
    new_reminder.save()
    pk1 = str(new_reminder.pk)
    rem = Reminder.find(Reminder.pk == pk1).first()
    return True

def save_idea(user,msg):
    print(msg)
    dt = datetime.now()
    epoch_time = int(round(dt.timestamp()))
    new_idea = Idea(user=user,message=msg,time=epoch_time)
    new_idea.save()
    return True

def start_timer(user,minutes):
    #dt = datetime.now().replace(tzinfo=tz)
    dt = datetime.now()
    dt += timedelta(minutes=minutes)
    print("HOUR ",dt.hour)
    epoch_time = int(round(dt.timestamp()))
    try:
        timer = Timer.find(Timer.user == user).first()
        if timer:
            return False
    except NotFoundError:
        return False

    new_timer = Timer(user=user,time=epoch_time)
    new_timer.save()
    return True

def save_note(user_pk,bag_pk,message):
    """ saves a note to the bag given for the user given """
    new_note = Note(user=user_pk,bag=bag_pk,message=message)
    new_note.save()
    return True

def create_notebag(user_pk,bag_name):
    """ returns the pk of the bag created """
    new_bag = NoteBag(user=user_pk,name=bag_name)
    new_bag.save()
    return new_bag.pk 

# --------------- DELETING -----------------------------------------------
#-------------------------------------------------------------------------
 
def delete_all_reminders():
    """
    deletes reminders in redis for ALL USERS
    """
    reminders = Reminder.find().all()
    for reminder in format_reminders(reminders):
        Reminder.delete(reminder['pk'])


def delete_user_reminders():
    """
    deletes reminders in redis for CURRENT USER
    """
    reminders = Reminder.find(Reminder.user == session['user']['pk']).all()
    for reminder in format_reminders(reminders):
        Reminder.delete(reminder['pk'])

def stop_timer(user_pk):
    try:
        timer = Timer.find(Timer.user == user_pk).first()
        if timer:
            Timer.delete(timer.pk)
    except NotFoundError:
        pass




# --------------- QUERYING -----------------------------------------------
#-------------------------------------------------------------------------


def all_reminders_this_minute():
    """ 
    gets reminders scheduled for current minute for ALL USERS 

    return: list[dict]
    """
    now = datetime.now().replace(tzinfo=tz)

    start = int(round(datetime(
        now.year,now.month,now.day,now.hour,now.minute,0)
        .timestamp()))

    end = int(round(
        datetime(now.year,now.month,now.day,now.hour,now.minute,59)
        .timestamp()))

    reminders = Reminder.find(
            (Reminder.time >= start) &
            (Reminder.time <= end)).all()
    return format_reminders(reminders)

def all_timers_this_minute():
    """
    gets timers scheduled for current minute for ALL USERS

    return: list[dict]
    """
    now = datetime.now().replace(tzinfo=tz)

    start = int(round(datetime(
        now.year,now.month,now.day,now.hour,now.minute,0)
        .timestamp()))

    end = int(round(
        datetime(now.year,now.month,now.day,now.hour,now.minute,59)
        .timestamp()))

    timers = Timer.find(
            (Timer.time >= start) &
            (Timer.time <= end)).all()

    return format_timers(timers)


def user_all_reminders(user_pk):
    """ gets all reminders current user has """
    reminders = Reminder.find(Reminder.user == user_pk).all()
    return format_reminders(reminders)

def user_all_ideas(user_pk):
    ideas = Idea.find(Idea.user == user_pk).all()
    return format_ideas(ideas)

def all_reminders():
    reminders = Reminder.find().all()
    return format_ideas(reminders)

def all_timers():
    timers = Timer.find().all()
    return format_timers(timers)
    

# ------------------------ SENDING ---------------------------------
#-------------------------------------------------------------------

def call(to,msg):
    """ sends a call to number "to" """
    call = client.calls.create(
            twiml='<Response><Say>{}</Say></Response>'.format(msg),
            to=to,
            from_=config.get('TWILIO_PHONE_NUMBER'))

def text(to, msg):
    """ sends a message "msg" to number "to" """
    message = client.messages.create(
            body=msg,
            from_=config.get('TWILIO_PHONE_NUMBER'),
            to=to)


def send_code(to):
    """ sends authorization code to "to" number 
        and saves the hashed code to session
    """
    user = session.get('user',default=dict())
    token = random.randrange(10000,99999)
    hash_code = generate_password_hash(str(token))
    session['code'] = hash_code
    text(to,f"Code:\n {token}")
    flash("Code sent!")

# ------------------- TESTING -----------------------------------
#----------------------------------------------------------------

def load_test_data():
    dt = datetime.now().replace(tzinfo=tz)
    
    dt -= timedelta(days=1)
    save_reminder(session['user']['pk'],"reminder yesterday",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))
    dt += timedelta(days=1)
    save_reminder(session['user']['pk'],"reminder today",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))
    dt += timedelta(minutes=2)
    save_reminder(session['user']['pk'],"reminder today in 2 minutes",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))
    dt += timedelta(minutes=1)
    save_reminder(session['user']['pk'],"reminder today in 3 minutes",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))
    dt -= timedelta(minutes=3)
    dt += timedelta(days=1)
    save_reminder(session['user']['pk'],"reminder tomorrow",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))






