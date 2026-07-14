from celery import Celery, Task
from celery.schedules import crontab

from app import create_app
import config

# ── Flask app (each task runs inside this app's context) ───────────────────────
flask_app = create_app()

class FlaskTask(Task):
    def __call__(self, *args, **kwargs):
        with flask_app.app_context():
            return self.run(*args, **kwargs)


# ── Celery app, wired directly to Redis ─────────────────────────────────────────
celery = Celery(
    flask_app.import_name,
    broker=config.CELERY_BROKER_URL,          # redis://localhost:6379/0
    backend=config.CELERY_RESULT_BACKEND,     # redis://localhost:6379/1
    include=['tasks'],
    task_cls=FlaskTask,
)

celery.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    broker_connection_retry_on_startup=True,
    timezone='Asia/Kolkata',
    enable_utc=False,
)

# ── Beat schedule ──────────────────────────────────────────────────────────────
celery.conf.beat_schedule = {
    'send-daily-reminders': {
        'task': 'tasks.send_daily_reminders',
        # 'schedule': crontab(hour=10, minute=30),
        'schedule': crontab(minute='*'),
    },
    'generate-monthly-report': {
        'task': 'tasks.generate_monthly_report',
        # 'schedule': crontab(day_of_month='1', hour=3, minute=0),
        'schedule': crontab(minute='*'),
    },
}

flask_app.extensions['celery'] = celery