from __future__ import absolute_import

# CELERY_RESULT_BACKEND = 'amqp://hourong:1220@10.10.114.35/celery'
# BROKER_URL = 'amqp://hourong:1220@10.10.114.35/celery'
# CELERY_RESULT_BACKEND = 'amqp://hourong:1220@10.10.189.213/celery'
BROKER_URL = 'amqp://hourong:1220@10.10.189.213/celery'

CELERY_RESULT_BACKEND = "mongodb"
CELERY_MONGODB_BACKEND_SETTINGS = {
    "host": "10.10.231.105",
    "port": 27017,
    "database": "Backend",
    "store_task": "store_task",
}
# BROKER_URL = 'redis://127.0.0.1:6379/10'
from kombu import Queue, Exchange

# CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/7'
# BROKER_URL = 'redis://127.0.0.1:6379/8'
# BROKER_URL = 'amqp://hourong:1220@10.10.213.148/celery'

# BROKER_URL = [
#     'amqp://hourong:1220@10.10.231.105/celery',
#     'amqp://hourong:1220@10.10.213.148/celery',
#     'amqp://hourong:1220@10.10.189.213/celery'
# ]
CELERYD_MAX_TASKS_PER_CHILD = 40
# CELERY_IGNORE_RESULT = True
CELERY_ACCEPT_CONTENT = ['pickle']
CELERY_TASK_SERIALIZER = 'pickle'
CELERY_MESSAGE_COMPRESSION = 'gzip'
# CELERY_QUEUE_HA_POLICY = 'all'
# task_queue_ha_policy = 'all'
CELERYD_POOL_RESTARTS = True
CELERY_EVENT_QUEUE_TTL = 5
