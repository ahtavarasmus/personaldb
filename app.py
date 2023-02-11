import celery
from flask import Flask, render_template, request, session, url_for
from reminder import Reminder
from redis_om import Migrator
from datetime import datetime,timezone,timedelta
from celery import Celery
from celery.schedules import crontab
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
import os


tz =  timezone(timedelta(hours=2))
twilio_account_sid = os.environ.get('TWILIO_ACCOUNT_SID')
twilio_auth_token = os.environ.get('TWILIO_AUTH_TOKEN')
twilio_client = Client(twilio_account_sid, twilio_auth_token)

app = Flask(__name__)
app.config['SECRET_KEY'] = "asdfasdfa"
celery_app = Celery('app',broker=os.environ.get('REDIS_OM_URL'))
celery_app.conf.update(
        timezone='Europe/Helsinki')

# TO RUN: $ celery -A app.celery_app worker -B -l info
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender,**kwargs):
    sender.add_periodic_task(crontab(),every_minute.s(),expires=10)


@celery_app.task
def add(x,y):
    return x+y

@celery_app.task
def every_minute():
    send_reminders()

def call_me():
    call = twilio_client.calls.create(
            url='http://demo.twilio.com/docs/voice.xml',
            to=os.environ.get('MY_PHONE_NUMBER'),
            from_=os.environ.get('TWILIO_PHONE_NUMBER')
        )

def text_me():
    message = twilio_client.messages.create(
            body="message",
            messaging_service_sid=os.environ.get('TWILIO_MGS_SID'),
            to=os.environ.get('MY_PHONE_NUMBER')
        )

def send_reminders():
    reminders = this_minute()
    for reminder in reminders:
        print("SENDING REMINDER:",reminder['message'])


def build_results(reminders):
    response = []
    for reminder in reminders:
        rem_dict = reminder.dict()
        print(rem_dict)
        rem_dict['time'] = datetime.fromtimestamp(rem_dict['time'])
        response.append(rem_dict)

    return response

def save_reminder(msg,time_str):
    time_obj = datetime.strptime(time_str, "%d/%m/%y %H:%M").replace(tzinfo=tz)
    epoch_time = int(round(time_obj.timestamp()))
    new_reminder = Reminder(message=msg,time=epoch_time)
    new_reminder.save()
    print(new_reminder.pk)

def load_test_data():
    dt = datetime.now().replace(tzinfo=tz)
    
    
    dt -= timedelta(days=1)
    save_reminder("reminder yesterday",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))
    dt += timedelta(days=1)
    save_reminder("reminder today",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))
    dt += timedelta(minutes=2)
    save_reminder("reminder today in 2 minutes",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))
    dt += timedelta(minutes=1)
    save_reminder("reminder today in 3 minutes",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))
    dt -= timedelta(minutes=3)
    dt += timedelta(days=1)
    save_reminder("reminder tomorrow",
                  str(dt.day)+"/"+str(dt.month)+"/"+str(dt.year)[2:]
                  +" "+str(dt.hour)+":"+str(dt.minute))

def delete_reminders():
    reminders = Reminder.find().all()
    for reminder in build_results(reminders):
        Reminder.delete(reminder['pk'])



@app.route("/",methods=['GET','POST'])
def home():

    reminders = all_reminders() 

    if request.method == 'POST':
        if "test-data" in request.form:
            load_test_data()
            reminders = all_reminders()
        elif "all" in request.form:
            reminders = all_reminders()
        elif "today" in request.form:
            reminders = today()
        elif "this-hour" in request.form:
            reminders = this_hour()
        elif "this-minute" in request.form:
            reminders = this_minute()
        elif "delete-data" in request.form:
            delete_reminders()
            reminders = all_reminders()
        elif "call-me" in request.form:
            call_me()
        elif "text-me" in request.form:
            text_me()
        else:
            msg = request.form['message']
            time_str = request.form['time']
            save_reminder(msg,time_str)
        return render_template("index.html",reminders=reminders)


    return render_template("index.html",
                           reminders=reminders)

@app.route("/sms-webhook/", methods=['POST','GET'])
def incoming_sms():

    body = request.values.get('Body',None)
    print("HELLO")
    
    if not body:
        return 

    # new reminder
    reply = 'Error! Was the message formatted right(ignore brackets): \
                "[keyletter] [day/month/year_two_digits] [hour:minute]" ?'
    if body[0] == 'r' and body[1] == ' ':
        parts = body[2:].split()
        time = parts[0]+" "+parts[1]
        msg = ""
        for part in parts[2:]:
            if part != parts[-1]: 
                msg += (part+" ")
            else: 
                msg += part

        if save_reminder(msg,time):
            reply = 'Reminder: "{}" added with time "{}".'.format(msg,time)

    resp = MessagingResponse()
    resp.message(reply)

    return str(resp)
    



# gets all the reminders scheduler for today
def today():
    now = datetime.now().replace(tzinfo=tz)
    
    start = int(round(datetime(now.year,now.month,now.day,0,0,0)
                      .timestamp()))

    end = int(round(datetime(now.year,now.month,now.day,23,59,59).timestamp()))

    reminders = Reminder.find((Reminder.time >= start) & (Reminder.time <= end)).all()

    return build_results(reminders)

def this_hour():
    now = datetime.now().replace(tzinfo=tz)

    start = int(round(datetime(now.year,now.month,now.day,now.hour,0,0)
                      .timestamp()))

    end = int(round(datetime(now.year,now.month,now.day,now.hour,59,59)
                    .timestamp()))

    reminders = Reminder.find((Reminder.time >= start) & (Reminder.time <= end)).all()
    return build_results(reminders)

def this_minute():
    now = datetime.now().replace(tzinfo=tz)

    start = int(round(datetime(now.year,now.month,now.day,now.hour,now.minute,0)
                      .timestamp()))

    end = int(round(datetime(now.year,now.month,now.day,now.hour,now.minute,59)
                    .timestamp()))

    reminders = Reminder.find((Reminder.time >= start) & (Reminder.time <= end)).all()
    print(reminders)
    return build_results(reminders)



def all_reminders():

    reminders = Reminder.find().all()

    return build_results(reminders)


Migrator().run()
