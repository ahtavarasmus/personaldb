# External
from flask import session,flash,send_file
from pydantic import NonNegativeFloat
from twilio.rest import Client
from redis_om import NotFoundError
from werkzeug.security import (check_password_hash, generate_password_hash)
from operator import itemgetter
from time import sleep
import requests
import re
import pytz
import json
import openai
import random

# Internal
from .models import Reminder,User,Idea,Timer,Note,NoteBag,Quote,Post
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
def utc_epoch_to_local_datetime(user_pk,epoch_time_utc):
    """
    turns epoch timestamps in utc into datetime objects using user's timezone
    return datetime, None if user not found
    """
    try:
        user = User.find(User.pk == user_pk).first()
    except:
        return None 
    timezone = pytz.timezone(user.timezone)
    time_obj_utc = datetime.fromtimestamp(int(epoch_time_utc))
    time_obj_local = time_obj_utc.astimezone(timezone)
    return time_obj_local

def to_utc_epoch(user_pk,time_str="now"):
    """
    param user_pk: str, user id
    param time_str: str, time formatted "day/month/year_last_two_nums hour:minute"
    return epoch time in UTC: int/None
        -> if time_str empty == current time
    """

    user = User.find(User.pk == user_pk).first()
    timezone = pytz.timezone(user.timezone)

    if time_str == "now":
        time_obj_utc = datetime.now(pytz.utc)
        # current time in UTC
    else:
        try:
            time_obj = datetime.strptime(time_str, "%d/%m/%y %H:%M")
            time_obj = timezone.localize(time_obj)
            time_obj_utc = time_obj.astimezone(pytz.utc)
        except ValueError:
            return None 

    time_obj_minute = time_obj_utc.replace(second=0, microsecond=0)
    epoch_time = int(round(time_obj_minute.timestamp()))
    return epoch_time


def save_reminder_text(user_pk,reminder_text):
    """ saves the reminder text as a reminder
    param user_pk: str, user id
    param reminder_text: str, reminder text
    return: bool, True if saved, False if not
    """
    reminder_format = turn_text_to_reminder_format(reminder_text)
    if correct_reminder_format(reminder_format):
        t = re.search(r"\d+\/\d+\/\d+",reminder_format)
        t2 = re.search(r"\d+\:\d+",reminder_format)
        if t == None or t2 == None:
            return False

        time = t.group() + " " + t2.group()
        msg = ""
        first_add = True
        for x in reminder_format.split():
            if x != t.group() and x != t2.group():
                if first_add:
                    msg += x
                    first_add = False
                else:
                    msg += " "+x

        save_reminder(user_pk,msg,time)
        return True
    return False



def process_speech(user_pk,user_phone):
    """ processes the speech to text and saves it as a reminder 
    param user_pk: str, user id
    param user_phone: str, user phone number
    return: bool, True if saved, False if not
    """
    text_rec = get_latest_recording(user_pk,user_phone)

    #TODO process what the text means here 
    if save_reminder_text(user_pk,text_rec):
        return True
    return False

def turn_text_to_reminder_format(text):
    cur_d = datetime.now(tz)
    cur_date = str(cur_d.day) + "/" + str(cur_d.month) + "/" + str(cur_d.year)[2:]
    response = openai.ChatCompletion.create(
          model="gpt-4",
          messages=[
              {"role": "system", "content": f"You turn given text prompts into reminder message and date and time, formatted as '<message> <day>/<month>/<year_last_two_numbers> <hour_in_24_format>:<minutes>'. For example given prompt 'a day after new year 2023 12pm there is a conference' would be turned into 'conference 2/1/23 12:00'. Date is formatted in order: day/month/year hour/minute. You are using timezone UTC+2h. The date at this moment is {cur_date}, so figure out from that the date and time the text means. Output only the reminder message, day and time and nothing else."},
                {"role": "user", "content": "7am the day after new year 2023 remind me that i got this"},
                {"role": "assistant", "content": "you got it 2/1/23 7:00"},
                {"role": "user", "content": f"{text}"},
            ]
        )
    return response["choices"][0]["message"]["content"]



def get_latest_recording(user_pk,phn):
    sleep(20)
    text_rec = latest_recording_text()
    return text_rec

def correct_reminder_format(text):
    t = re.search(r"\d+\/\d+\/\d+",text)
    t2 = re.search(r"\d+\:\d+",text)

    if t == None or t2 == None:
        return False
    return True

def get_user_data(user_pk):
    reminders = user_all_reminders(user_pk)
    ideas = user_all_ideas(user_pk)
    notebags = user_all_notebags(user_pk)
    quotes = user_all_quotes(user_pk)
    links = user_all_links(user_pk)

    return reminders, ideas, notebags, quotes,links

      


def handle_request_form(request_form, user_pk,item_pk):
    if "bag-name" in request_form:
        name = request_form.get("bag-name")
        save_notebag(user_pk, name)

def format_quotes(quotes):
    response = []
    for quote in quotes:
        q_dict = quote.dict()
        response.append(q_dict)
    return response


def format_ideas(ideas):
    """
    Receives a list of idea json objects
    and turns them into list of dicts
    """
    response = []
    for idea in ideas:
        i_dict = idea.dict()
        new_time = utc_epoch_to_local_datetime(i_dict['user'],i_dict['time'])
        if new_time:
            i_dict['time'] = new_time
        else:
            continue
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
        new_time = utc_epoch_to_local_datetime(rem_dict['user'],rem_dict['time'])
        if new_time:
            rem_dict['time'] = new_time
        else:
            delete_reminder(rem_dict['pk'])
            continue
        response.append(rem_dict)


    response = sorted(response, key=itemgetter('time'), reverse=True)
    return response

def format_timers(timers):
    
    response = []
    for timer in timers:
        timer_dict = timer.dict()

        new_time = utc_epoch_to_local_datetime(timer['user'],timer['time'])
        timer['time'] = new_time
        response.append(timer_dict)

    return response

def format_notebags(notebags):
    response = []
    for bag in notebags:
        bag_dict = bag.dict()
        for note in bag_dict['notes']:
            user = session.get('user',default="")
            new_time = utc_epoch_to_local_datetime(user,note['time'])
            note['time'] = new_time

        response.append(bag_dict)

    # sort
    for bag in response:
        bag['notes'] = sorted(bag['notes'],key=itemgetter('time'),reverse=True)

    return response

def format_posts(posts):
    response = []
    for post in posts:
        post_dict = post.dict()

        new_time = utc_epoch_to_local_datetime(post_dict['user'],post_dict['time'])
        post_dict['time'] = new_time
        response.append(post_dict)

    response = sorted(response, key=itemgetter('time'), reverse=True)
    return response




def move_note(user_pk,note_pk,bag_name):
    user = User.find(User.pk == user_pk).first()
    for bag in user.notebags:
        for note in bag.notes:
            if note.pk == note_pk:
                save_note(user.pk,bag_name,note.message,note.time)
                delete_note(user.pk,note_pk)
                return True
    return False

# --------------- SAVING -------------------------------------------------
#-------------------------------------------------------------------------

def save_post(user_pk,img):
    ICI = config.get('IMGUR_CLIENT_ID')
    headers = {'Authorization': f'Client-ID {ICI}'}
    url = 'https://api.imgur.com/3/image'
    payload = {'image': img.read()}

    if img:
        response = requests.post(url, headers=headers, data=payload)

        if response.status_code == 200:
            image_id = response.json()['data']['link']
            new_post = Post(user=user_pk,imgur_url=image_id)
            new_post.save()
            return image_id


    return None

def save_link(user_pk,link):
    try:
        user = User.find(User.pk == user_pk).first()
    except NotFoundError:
        flash("couldn't find the user")
        return False
    user.links.append(link)
    user.save()
    flash("link saved")
    return True

def save_quote(user_pk,msg):
    try:
        user = User.find(User.pk == user_pk).first()
    except:
        flash("couldn't find the user")
        return False
    q = Quote(quote=msg)
    user.quotes.append(q)
    user.save()
    flash("quote saved")
    return True
    

def save_reminder(user_pk,msg,time_str,reoccurring="false",remind_method="text"):
    """
    saves a reminder to redis
    return: True if success, else False
    """
    epoch_time = to_utc_epoch(user_pk,time_str)
    if not epoch_time:
        return False
    new_reminder = Reminder(user=user_pk,
                            message=msg,
                            time=epoch_time,
                            reoccurring=reoccurring,
                            remind_method=remind_method
                            )
    new_reminder.save()
    flash('reminder saved')
    return True

def save_idea(user,msg):
    dt = datetime.now()
    epoch_time = int(round(dt.timestamp()))
    new_idea = Idea(user=user,message=msg,time=epoch_time)
    new_idea.save()
    flash('idea saved')
    return True

def start_timer(user,minutes):
    #dt = datetime.now().replace(tzinfo=tz)
    dt = datetime.now()
    dt += timedelta(minutes=minutes)
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

def save_notebag(user_pk, name):
    try:
        user = User.find(User.pk == user_pk).first()
    except NotFoundError:
        return False
    for notebag in user.notebags:
        if notebag.name == name:
            flash('name exists already')
            return False
    user.notebags.append(NoteBag(name=name))
    user.save()
    flash('notebag saved')
    return True

def save_note(user_pk, bag_name, message,time=str(round(datetime.now().timestamp()))):
    try:
        user = User.find(User.pk == user_pk).first()
    except NotFoundError:
        return False

    found = False
    for bag in user.notebags:
        if bag.name == bag_name:
            bag.notes.append(Note(message=message,time=time))
            user.save()
            found = True
            break
    if found:
        flash('note saved')
        return True
    return False




# --------------- DELETING -----------------------------------------------
#-------------------------------------------------------------------------

def delete_reminder(rem_pk):
    """ Deletes the reminder with the given id """
    Reminder.delete(rem_pk)
    flash('reminder deleted')
 
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

def delete_note(user_pk,note_pk):
    try:
        user = User.find(User.pk == user_pk).first()
    except:
        return False

    for notebag in user.notebags:
        for note in notebag.notes:
            if note.pk == note_pk:
                notebag.notes.remove(note)
                user.save()
                flash('note deleted')
                return True

    return False 

def delete_notebag(user_pk,bag_name):
    try:
        user = User.find(User.pk == user_pk).first()
    except:
        return False

    for notebag in user.notebags:
        if notebag.name == bag_name:
            user.notebags.remove(notebag)
            user.save()
            flash('notebag deleted')
            return True

    return False

def delete_post(post_pk):
    Post.delete(post_pk)
    flash("post deleted")



# --------------- QUERYING -----------------------------------------------
#-------------------------------------------------------------------------


def all_reminders_this_minute():
    """ 
    gets reminders scheduled for current minute for ALL USERS 

    return: list[dict]
    """
    now = datetime.now(pytz.utc)

    start = int(round(now.replace(second=0,microsecond=0).timestamp()))
    end = int(round(now.replace(second=59,microsecond=0).timestamp()))

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
    return format_reminders(reminders)

def all_timers():
    timers = Timer.find().all()
    return format_timers(timers)
    
def user_all_notebags(user_pk):
    notebags = User.find(User.pk == user_pk).first().notebags
    return format_notebags(notebags)

def user_all_quotes(user_pk):
    quotes = User.find(User.pk == user_pk).first().quotes
    return format_quotes(quotes)

def user_all_links(user_pk):
    links = User.find(User.pk == user_pk).first().links
    return links

def user_all_posts(user_pk):
    posts = Post.find(Post.user == user_pk).all()
    return format_posts(posts)


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



def latest_recording_text():
    recs = client.recordings.list()
    latest = recs[0]
    recording_url = latest.uri.replace('.json','.mp3')
    recording_url = f'https://api.twilio.com{recording_url}'
        # Download the file
    response = requests.get(recording_url, stream=True)

    # Create a temporary file to store the downloaded file
    local_file = 'temp_recording.mp3'
    with open(local_file, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    audio_file = open(local_file, "rb")
    transcript = openai.Audio.translate(
                            model = "whisper-1", 
                            file = audio_file,
                            options = {
                        "language" : "en",           # this is ISO 639-1 format as recommended in the docs
                        "response_format" : "json",
                        "temperature" : "0"
                        })

    return transcript.text

