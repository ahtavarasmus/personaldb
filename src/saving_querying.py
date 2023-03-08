from . import tz
from datetime import datetime
from .models import Reminder,User,Idea
from .messaging import *
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
    new_reminder = Reminder(user=user_pk,
                            message=msg,
                            time=epoch_time
                            )
    new_reminder.save()
    pk1 = str(new_reminder.pk)
    rem = Reminder.find(Reminder.pk == pk1).first()
    return True

 
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




