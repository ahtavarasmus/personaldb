from .utils import *
from random import shuffle
from .models import User
from celery import shared_task


@shared_task
def every_minute():
    # --------------------- REMINDERS -----------------------------
    reminders = all_reminders_this_minute()
    for rem in reminders:
        try:
            userr = User.find(User.pk == rem['user']).first()
            user = userr.dict()
        except:
            continue
        if rem['remind_method'] == "call":
            call(str(user['phone']),rem['message'])
        else: # text
            msg = rem['message']
            if msg == "quote":
                quotes = user_all_quotes(user['pk'])
                shuffle(quotes)
                msg = quotes[0]
            text(str(user['phone']),msg)
        if rem['reoccurring'] == "true":
            new_time = int(round((rem['time']+timedelta(days=1)).timestamp()))
            new_reminder = Reminder(user=rem['user'],
                            message=rem['message'],
                            time=new_time,
                            reoccurring=rem['reoccurring'],
                            remind_method=rem['remind_method']
                            )
            new_reminder.save()

        delete_reminder(rem['pk'])







    # ------------------------TIMER -------------------------------
    timers = all_timers_this_minute()
    for timer in timers:
        try:
            user = User.find(User.pk == timer['user']).first()
            user = user.dict()
        except:
            continue
        call(str(user['phone']),"timer finished")
        stop_timer(user['pk'])



    print("HAHAHAHAH")


