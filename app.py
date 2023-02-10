from flask import Flask, render_template, request, session, url_for
from redis.cluster import READ_COMMANDS
import requests
from pydantic import ValidationError
import json
from reminder import Reminder
from redis_om import Migrator
from datetime import datetime,timezone,timedelta
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = "asdfasdfa"

# tz =  timezone(timedelta(hours=2))


def build_results(reminders):
    response = []
    for reminder in reminders:
        response.append(reminder.dict())
    return response

def save_reminder(msg,time_str):
    time_obj = datetime.strptime(time_str, "%d/%m/%y %H:%M")
    new_reminder = Reminder(message=msg,time=time_obj)
    new_reminder.save()
    print(new_reminder.pk)

def load_test_data():
    save_reminder("reminder yesterday","9/2/23 23:00")
    save_reminder("reminder today","10/2/23 23:00")
    save_reminder("reminder tomorrow","11/2/23 23:00")


@app.route("/",methods=['GET','POST'])
def home():

    reminders = all_reminders() 

    if request.method == 'POST':
        if "test-data" in request.form:
            load_test_data()
        elif "all" in request.form:
            reminders = all_reminders()
        elif "today" in request.form:
            reminders = today()
        elif "this-hour" in request.form:
            reminders = this_hour()
        else:
            msg = request.form['message']
            time_str = request.form['time']
            save_reminder(msg,time_str)

    return render_template("index.html",
                           reminders=reminders)


# gets all the reminders scheduler for today
def today():
    now = datetime.now()

    start = datetime(now.year,now.month,now.day,0,0,0)

    end = datetime(now.year,now.month,now.day,23,59,59)

    reminders = Reminder.find(Reminder.time >= start and Reminder.time <= end)

    return reminders


def this_hour():
    now = datetime.now()

    start = datetime(
            now.year,
            now.month,
            now.day,
            now.hour,
            0,0)

    end = datetime(
            now.year,
            now.month,
            now.day,
            now.hour,
            59,59)

    # this is a way around it, but it would be nice to know why today()
    # doesn't work
    all_reminders = build_results(Reminder.find().all())
    reminders = []
    for reminder in all_reminders:
        if reminder['time'] >= start and reminder['time'] <= end:
            reminders.append(reminder)

    return reminders


def all_reminders():

    reminders = Reminder.find().all()

    return build_results(reminders)


Migrator().run()
