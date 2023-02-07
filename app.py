from flask import Flask, render_template, request, session
from pydantic import ValidationError
import json
from reminder import Reminder
from redis_om import Migrator
from datetime import datetime

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
    #new_message = request.form['message']
    #msg_time = request.form['time']
    # date format "7/2/23 0:20"
    #reminder_json = json.dumps({"message": new_message,"time":msg_time,"call":True})

    try:
        #print(reminder_json)
        new_reminder = Reminder(**request.json)
        new_reminder.save()
        return new_reminder.pk

    except ValidationError as e:
        print(e)
        return "Wasn't able to create reminder.",400


@app.route("/",methods=['GET','POST'])
def home():

    if 'reminders' not in session:
        session['reminders'] = all_reminders()
    reminders = session['reminders']

    if request.method == 'POST':
        reminders = all_reminders()
        if request.form['time_point'] == 'today':
            reminders = today()
        elif request.form['time_point'] == 'now':
            reminders = now()
        session['reminders'] = reminders

    return render_template("index.html",reminders=reminders)


# gets all the reminders scheduler for today
def today():
    todays_date = datetime.now().day
    reminders = Reminder.find(turn_to_datetime(Reminder.time).day == todays_date).all()
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
