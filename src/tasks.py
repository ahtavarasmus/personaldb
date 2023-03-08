from .messaging import all_reminders_this_minute,text,call
from .saving_querying import all_timers_this_minute,stop_timer
from .models import User
from celery import shared_task


@shared_task
def every_minute():
    # --------------------- REMINDERS -----------------------------
    reminders = all_reminders_this_minute()
    for rem in reminders:
        try:
            user = User.find(User.pk == rem['user']).first()
            user = user.dict()
        except:
            continue
        text(str((user['phone'])),rem['message'])


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


