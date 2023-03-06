from .messaging import all_reminders_this_minute
from celery import shared_task

@shared_task
def every_minute():
    rs = all_reminders_this_minute()
    for r in rs:
        print("this")
        print("Reminder: ", r['message'])


