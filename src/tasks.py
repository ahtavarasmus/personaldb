from .messaging import all_reminders_this_minute,text
from .models import User
from celery import shared_task


@shared_task
def every_minute():
    reminders = all_reminders_this_minute()
    for rem in reminders:
        try:
            user = User.find(User.pk == rem['user']).first()
            user = user.dict()
        except:
            continue
        print("Reminder: ", rem['message'])
        text(str((user['phone'])),rem['message'])
    print("HAHAHAHAH")


