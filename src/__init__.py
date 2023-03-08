from flask import Flask,session
from redis_om import Migrator
from celery import Celery,Task,shared_task
from celery.schedules import crontab
from datetime import datetime,timedelta,timezone
from .messaging import all_reminders_this_minute
import json

with open('/etc/personaldb_config.json') as config_file:
    config = json.load(config_file)


tz = timezone(timedelta(hours=2))

# ---------------- CREATE APP ----------------

def create_app():
    app = Flask(__name__)
    app.config.from_file("/etc/personaldb_config.json", load=json.load)
    app.config['CELERY_BROKER_URL'] = config.get('REDIS_OM_URL')
    app.config.from_mapping(CELERY=dict(
            broker_url=config.get('REDIS_OM_URL'),
            result_backend=config.get('REDIS_OM_URL'),
            task_ignore_result=True,
        ),
    )

    celery_init_app(app)

    with app.app_context():
        from . import routes
        from . import auth
        from . import editing
        Migrator().run()

        app.register_blueprint(routes.routes)
        app.register_blueprint(auth.auth)
        app.register_blueprint(editing.editing)
        
        return app

# ---------------- CREATE CELERY APP -----------------


def celery_init_app(app: Flask) -> Celery:
    from . import tasks
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config['CELERY'])
    celery_app.conf.update(timezone='Europe/Helsinki')

    celery_app.set_default()

    celery_app.conf.beat_schedule = {
        'task-name': {
            'task':'src.tasks.every_minute',
            'schedule': crontab()
            }
    }
    #@celery_app.on_after_configure.connect
    #def setup_periodic_tasks(sender,**kwargs):
    #    #from .tasks import every_minute 
    #    sender.add_periodic_task(crontab(),every_minute.s())

    app.extensions["celery"] = celery_app
    return celery_app

