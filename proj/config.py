from __future__ import absolute_import

CELERY_RESULT_BACKEND = 'amqp://hourong:1220@10.10.213.148/celery'
BROKER_URL = 'amqp://hourong:1220@10.10.213.148/celery'
CELERYD_MAX_TASKS_PER_CHILD = 40
CELERY_IGNORE_RESULT = True
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_MESSAGE_COMPRESSION = 'gzip'

from datetime import timedelta

CELERYBEAT_SCHEDULE = {
    'add-image-url': {
        'task': 'proj.tasks.add_image_url',
        'schedule': timedelta(minutes=30),
        'args': ()
    },
}
