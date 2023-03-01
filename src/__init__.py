from flask import Flask,session
from redis_om import Migrator
from celery import Celery
from celery.schedules import crontab
from datetime import datetime,timedelta,timezone
import json

with open('/etc/personaldb_config.json') as config_file:
    config = json.load(config_file)


tz = timezone(timedelta(hours=2))

celery_app = Celery('app',broker=config.get('REDIS_OM_URL'))
celery_app.conf.update(timezone='Europe/Helsinki')

# TO RUN: $ celery -A app.celery_app worker -B -l info
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender,**kwargs):
    sender.add_periodic_task(crontab(),every_minute.s())

@celery_app.task
def every_minute():
    print("hahahahha")


# ---------------- CREATE APP ----------------

def create_app():
    app = Flask(__name__)
    app.config.from_file("/etc/personaldb_config.json", load=json.load)


    with app.app_context():
        from . import routes
        from . import auth
        Migrator().run()

        app.register_blueprint(routes.routes)
        app.register_blueprint(auth.auth)
        
        return app
