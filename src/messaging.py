from amqp import NotFound
from . import config,tz
from flask import session,flash
from redis_om.model import NotFoundError
from .models import Reminder,Idea,User,Timer
from datetime import datetime,timedelta
from werkzeug.security import (check_password_hash, generate_password_hash)
from twilio.rest import Client
import random

client = Client(config.get('TWILIO_ACCOUNT_SID'),
                    config.get('TWILIO_AUTH_TOKEN'))

# --------------- SAVING/DELETING STUFF ------------------

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
    new_reminder = Reminder(user=user_pk,message=msg,time=epoch_time)
    new_reminder.save()
    print(new_reminder.pk)
    return True

 
def delete_all_reminders():
    """
    deletes reminders in redis for ALL USERS
    """
    print("HEre")
    reminders = Reminder.find().all()
    for reminder in format_reminders(reminders):
        print("DELETING:",reminder['pk'])
        Reminder.delete(reminder['pk'])


def delete_user_reminders():
    """
    deletes reminders in redis for CURRENT USER
    """
    reminders = Reminder.find(Reminder.user == session['user']['pk']).all()
    for reminder in format_reminders(reminders):
        print("DELETING:",reminder['pk'])
        Reminder.delete(reminder['pk'])


def save_idea(user,msg):
    print(msg)
    new_idea = Idea(user=user,message=msg)
    new_idea.save()
    return True

def start_timer(user,minutes):
    dt = datetime.now().replace(tzinfo=tz)
    dt += timedelta(minutes=minutes)
    epoch_time = int(round(dt.timestamp()))
    try:
        timer = Timer.find(Timer.user == user).first()
        if timer:
            return False
    except NotFoundError:
        pass

    new_timer = Timer(user=user,time=epoch_time)
    new_timer.save()
    return True

def stop_timer(user):
    try:
        timer = Timer.find(Timer.user == user).first()
        if timer:
            Timer.delete(timer.pk)
    except NotFoundError:
        pass




# ----------------------- OUTPUT ----------------------

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




# --------------------- QUERIES -----------------------

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

def user_all_reminders(user_pk):
    """ gets all reminders current user has """
    reminders = Reminder.find(
            Reminder.user == user_pk).all()

    return format_reminders(reminders)

def user_all_ideas(user_pk):
    ideas = Idea.find(Idea.user == user_pk).all()
    return format_ideas(ideas)



# -------------------- UTILITY FUNCTIONS ----------------------

def format_ideas(ideas):
    response = []
    for idea in ideas:
        i_dict = idea.dict()
        response.append(i_dict)
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

    return response


# ------------------- TESTING -----------------------


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


