import json
import redis
from flask import current_app


def notify_application_update(application):
    """Publishes a Redis pub/sub event so the applicant's open SSE connection (if any) can refresh."""
    client = redis.Redis.from_url(current_app.config['CACHE_REDIS_URL'])
    channel = f'student-updates:{application.student.user_id}'
    client.publish(channel, json.dumps({'application_id': application.id}))
