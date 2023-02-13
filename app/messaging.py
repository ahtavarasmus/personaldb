from . import twilio_client,config,tz
from .models import Reminder
from datetime import datetime,timedelta


def call(to):
    """ sends a call to number "to" """
    call = twilio_client.calls.create(
            url='http://demo.twilio.com/docs/voice.xml',
            to=to,
            from_=config.get('TWILIO_PHONE_NUMBER'))
def text(to, msg):
    """ sends a message "msg" to number "to" """
    message = twilio_client.messages.create(
            body=msg,
            messaging_service_sid=config.get('TWILIO_MGS_SID'),
            to=to)

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

def save_reminder(user_pk,msg,time_str):
    """
    saves a reminder to redis

    return: True if success, else False
    """
    try:
        time_obj = datetime.strptime(time_str, "%d/%m/%y %H:%M").replace(tzinfo=tz)
    except ValueError:
        return False
    epoch_time = int(round(time_obj.timestamp()))
    new_reminder = Reminder(user=user_pk,message=msg,time=epoch_time)
    new_reminder.save()
    print(new_reminder.pk)
    return True

    

def delete_reminders():
    """
    deletes all reminders in redis
    """
    reminders = Reminder.find().all()
    for reminder in format_reminders(reminders):
        Reminder.delete(reminder['pk'])


def reminders_this_minute():
    """ 
    gets all the reminders scheduled for current minute 

    return: list[dict]
    """
    now = datetime.now().replace(tzinfo=tz)

    start = int(round(datetime(
        now.year,now.month,now.day,now.hour,now.minute,0)
        .timestamp()))

    end = int(round(
        datetime(now.year,now.month,now.day,now.hour,now.minute,59)
        .timestamp()))

    reminders = Reminder.find((Reminder.time >= start) &
                              (Reminder.time <= end)).all()
    print(reminders)
    return format_reminders(reminders)


# gets all the reminders scheduler for today
def reminders_today():
    """ 
    gets all the reminders scheduled for today 

    return: list[dict]
    """
    now = datetime.now().replace(tzinfo=tz)
    
    start = int(round(datetime(
        now.year,now.month,now.day,0,0,0)
        .timestamp()))

    end = int(round(datetime(
        now.year,now.month,now.day,23,59,59)
        .timestamp()))

    reminders = Reminder.find((Reminder.time >= start) &
                              (Reminder.time <= end)).all()

    return format_reminders(reminders)



def all_reminders():

    reminders = Reminder.find().all()

    return format_reminders(reminders)






