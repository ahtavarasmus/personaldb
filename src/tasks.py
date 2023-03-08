from .messaging import all_reminders_this_minute
from celery import shared_task


@shared_task
def every_minute():
    reminders = all_reminders_this_minute()
    for rem in reminders:
        print("Reminder: ", rem['message'])
    print("HAHAHAHAH")


