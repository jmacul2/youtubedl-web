import os
import json

from flask import Config
from celery import Celery
from werkzeug.debug import DebuggedApplication
from project.common.base import BaseFlask

# flask config
from dotenv import load_dotenv
load_dotenv()
conf = Config(root_path=os.path.dirname(os.path.realpath(__file__)))
conf.from_object(os.getenv('APP_SETTINGS'))

from project.extensions import db


def create_app():
    # instantiate the app
    app = BaseFlask(__name__)

    # configure interactive debugger
    if app.debug:
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

    # register extensions
    db.init_app(app)

    # register blueprints
    from project.views.index import blueprint as index_bp
    from project.views.api import blueprint as api_bp
    app.register_blueprint(index_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # register commands
    from project.commands import cli
    app.cli.add_command(cli)

    # register error handlers
    from project.common import exceptions
    from project.common import error_handlers
    app.register_error_handler(exceptions.InvalidPayload, error_handlers.handle_exception)
    app.register_error_handler(exceptions.BusinessException, error_handlers.handle_exception)
    app.register_error_handler(exceptions.UnauthorizedException, error_handlers.handle_exception)
    app.register_error_handler(exceptions.ForbiddenException, error_handlers.handle_exception)
    app.register_error_handler(exceptions.NotFoundException, error_handlers.handle_exception)
    if not app.config['DEBUG']:
        # Thise handlers hide errors that help with debuging
        app.register_error_handler(exceptions.ServerErrorException, error_handlers.handle_exception)
        app.register_error_handler(Exception, error_handlers.handle_general_exception)

    return app


# noinspection PyPropertyAccess
def make_celery(app):
    app = app or create_app()
    celery = Celery(
        __name__,
        broker=app.config['CELERY_BROKER_URL'], 
        include=['project.tasks'],
        backend=app.config['CELERY_RESULT_BACKEND']
    )
    celery.conf.update(app.config)
    from project.models import FailedTask
    TaskBase = celery.Task
    class ContextTask(TaskBase):
        abstract = True
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)
        def on_failure(self, exc, task_id, args, kwargs, einfo):
            self.save_failed_task(exc, task_id, args, kwargs, einfo)
            super(ContextTask, self).on_failure(exc, task_id, args, kwargs, einfo)
        def save_failed_task(self, exc, task_id, args, kwargs, traceback):
            '''
            Save record of failed tasks.
            https://gist.github.com/darklow/c70a8d1147f05be877c3
            '''
            with app.app_context():
                task = FailedTask(
                    task_id=task_id,
                    full_name=self.name,
                    name=self.name.split('.')[-1],
                    exception_class=exc.__class__.__name__,
                    exception_msg=str(exc).strip(),
                    traceback=str(traceback).strip(),
                )
                if args:
                    task.args = json.dumps(list(args))
                if kwargs:
                    task.kwargs = json.dumps(kwargs)
                # Find if task with same args, name and exception already exists
                # If it do, update failures count and last updated_at
                existing_task = FailedTask.query.filter_by(
                    args=task.args,
                    kwargs=task.kwargs,
                    full_name=task.full_name,
                    exception_class=task.exception_class,
                    exception_msg=task.exception_msg,
                ).all()
                if len(existing_task):
                    existing_task = existing_task[0]
                    existing_task.failures += 1
                    existing_task.updated_at = task.updated_at
                    existing_task.save()
                else:
                    task.save()
    celery.Task = ContextTask
    return celery


app = create_app()
celery = make_celery(app)
