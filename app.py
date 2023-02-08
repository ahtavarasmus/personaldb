from flask import Flask, render_template, request, session, url_for
import requests
from pydantic import ValidationError
import json
from reminder import Reminder
from redis_om import Migrator
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = "asdfasdfa"


def turn_to_datetime(time):
    return datetime.strptime(time,"%d/%m/%y %H:%M")


def build_results(reminders):
    response = []
    for reminder in reminders:
        response.append(reminder.dict())
    return {"results": response}


# creates new reminder
@app.route("/reminder/new",methods=['POST'])
def create_reminder():
    try:
        print(request.json)
        new_reminder = Reminder(**request.json)
        new_reminder.save()
        print(new_reminder.pk)
        return new_reminder.pk

    except ValidationError as e:
        print(e)
        return "Wasn't able to create reminder.",400


@app.route("/",methods=['GET','POST'])
def home():

    reminders = all_reminders()

    if request.method == 'POST':
        msg = request.form['message']
        time = request.form['time']
        reminder_json = json.dumps({"message":msg, "time":time})
        primary_key = requests.post(
                'http://127.0.0.1:5000/reminder/new',json=reminder_json)

    return render_template("index.html",reminders=reminders)


# gets all the reminders scheduler for today
def today():
    reminders = Reminder.find(
            turn_to_datetime(Reminder.time).day == datetime.now().day).all()
    return build_results(reminders)


def now():
    current_time = datetime.now()
    reminders = Reminder.find(
            turn_to_datetime(Reminder.time).year == current_time.year &
            turn_to_datetime(Reminder.time).month == current_time.month &
            turn_to_datetime(Reminder.time).day == current_time.day &
            turn_to_datetime(Reminder.time).hour == current_time.hour
            ).all()
    return build_results(reminders)


def all_reminders():
    reminders = Reminder.find().all()
    return build_results(reminders)


Migrator().run()
