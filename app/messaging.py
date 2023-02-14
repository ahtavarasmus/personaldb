from . import twilio_client,config,tz
from flask_login import current_user
from .models import Reminder
from datetime import datetime,timedelta

# -------------------- UTILITY FUNCTIONS ----------------------

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

# -------------------- FOR SPECIFIED USER -----------------------

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


    
# ------------------- FOR ALL USERS ------------------------
def delete_all_reminders():
    """
    deletes reminders in redis for ALL USERS
    """
    reminders = Reminder.find().all()
    for reminder in format_reminders(reminders):
        Reminder.delete(reminder['pk'])

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

# ----------------- FOR CURRENT USER ----------------------


def load_test_data():
    dt = datetime.now().replace(tzinfo=tz)
    
    dt -= timedelta(days=1)
    save_reminder(current_user['pk'],"reminder yesterday",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))
    dt += timedelta(days=1)
    save_reminder(current_user['pk'],"reminder today",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))
    dt += timedelta(minutes=2)
    save_reminder(current_user['pk'],"reminder today in 2 minutes",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))
    dt += timedelta(minutes=1)
    save_reminder(current_user['pk'],"reminder today in 3 minutes",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))
    dt -= timedelta(minutes=3)
    dt += timedelta(days=1)
    save_reminder(current_user['pk'],"reminder tomorrow",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))

def delete_user_reminders():
    """
    deletes reminders in redis for CURRENT USER
    """
    reminders = Reminder.find(Reminder.pk == current_user['pk']).all()
    for reminder in format_reminders(reminders):
        Reminder.delete(reminder['pk'])


def user_all_reminders():

    reminders = Reminder.find(Reminder.pk == current_user['pk']).all()

    return format_reminders(reminders)






