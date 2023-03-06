from src import create_app

flask_app = create_app()
celery_app = flask_app.extensions['celery']
flask_app.app_context().push()
#celery_app = flask_app.extensions['celery']
if __name__ == '__main__':
    celery_app.worker_main(['worker', '-B', '-l', 'info'])
