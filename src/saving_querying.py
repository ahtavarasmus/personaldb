from flask import session
from datetime import datetime,timedelta,timezone
from .models import Timer
from redis_om import NotFoundError
from .models import Reminder,User,Idea
from .utils import format_timers,format_reminders,format_ideas
# --------------- SAVING ------------------
# --------------- DELETING ------------------
# --------------- QUERYING ------------------
tz = timezone(timedelta(hours=2))


# --------------- SAVING ------------------------------------------------------
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
    new_idea = Idea(user=user,message=msg)
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
        pass

    new_timer = Timer(user=user,time=epoch_time)
    new_timer.save()
    return True


# --------------- DELETING ----------------------------------------------------
 
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


# --------------- QUERYING ----------------------------------------------------


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
    


