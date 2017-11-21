#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/6 下午9:01
# @Author  : Hou Rong
# @Site    :
# @File    : rabbitmq_watcher.py
# @Software: PyCharm
import sys

sys.path.append('/root/data/lib')
import json
import requests
import re
from proj.my_lib.logger import get_logger
from apscheduler.schedulers.blocking import BlockingScheduler
from requests.auth import HTTPBasicAuth
from proj.celery import app
from proj.my_lib.task_module.mongo_task_func import get_task_total_simple
from proj.my_lib.task_module.routine_task_func import get_routine_task_total
from monitor import monitoring_hotel_detail2ImgOrComment, monitoring_hotel_list2detail, \
    monitoring_poi_detail2imgOrComment, monitoring_poi_list2detail, monitoring_qyer_list2detail, \
    monitoring_supplement_field, monitoring_zombies_task, city2list
from proj.config import BROKER_URL
from proj.my_lib.Common.Task import Task

host, v_host = re.findall("amqp://.+?@(.+?)/(.+)", BROKER_URL)[0]
TARGET_URL = 'http://{0}:15672/api/queues/{1}'.format(host, v_host)

schedule = BlockingScheduler()

import datetime

# schedule.add_job(monitoring_supplement_field, 'date', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=10), id='monitoring_hotel_list')
# schedule.add_job(monitoring_hotel_list2detail, 'cron', second='*/45', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=50),id='monitoring_hotel_list')
# schedule.add_job(monitoring_hotel_detail2ImgOrComment, 'cron', second='*/90', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=150), id='monitoring_hotel_detail')
# schedule.add_job(monitoring_poi_list2detail, 'cron', second='*/45', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=25), id='monitoring_poi_list')
# schedule.add_job(monitoring_poi_detail2imgOrComment, 'cron', second='*/90', id='monitoring_poi_detail')
# schedule.add_job(monitoring_qyer_list2detail, 'cron', second='*/45', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=2), id='monitoring_qyer_detail')
# schedule.add_job(monitoring_supplement_field, 'cron', hour='*/2', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=7), id='monitoring_supplement_field')
schedule.add_job(city2list, 'cron', second='*/60', id='city2list')
schedule.add_job(monitoring_zombies_task, 'cron', second='*/60', id='monitoring_zombies_task')

# stream_handler = logging.StreamHandler()
# logger = logging.getLogger('rabbitmq_watcher')
# logger.addHandler(stream_handler)
# logger.setLevel(logging.DEBUG)
logger = get_logger("rabbitmq_watcher")
'''
用于管理分发任务的数目
默认为 default 值
key 任务队列名称 val (队列中最少的任务数，单次插入任务数，执行时间间隔)
'''
TASK_CONF = {
    'default': (0, 0, 10),
    'file_downloader': (36000, 40000, 10),
    'hotel_detail': (36000, 40000, 10),
    'hotel_list': (36000, 40000, 10),
    'poi_detail': (36000, 40000, 10),
    'poi_list': (36000, 40000, 10),
    'supplement_field': (9000, 40000, 10),
    'google_api': (9000, 40000, 10),
    'merge_task': (10000, 40000, 11)
}

MAX_RETRY_TIMES_CONF = {
    'hotel_list_task': 10,
}

QUEUE_MAX_COUNT = 50000

DEFAULT_MAX_RETRY_TIMES = 12


def get_max_retry_times(queue_name):
    return MAX_RETRY_TIMES_CONF.get(queue_name, DEFAULT_MAX_RETRY_TIMES)


def insert_task(queue, limit):
    _count = 0
    # max_retry_times = get_max_retry_times(queue_name=queue)
    for task in get_task_total_simple(
            queue=queue,
            limit=limit,
            used_times=6):

        _count += 1
        app.send_task(
            task.worker,
            task_id=task.task_id,
            kwargs={'task': task},
            queue=task.queue,
            routing_key=task.routine_key
        )
    logger.info("Insert queue: {0} task count: {1}".format(queue, _count))


def mongo_task_watcher(*args):
    logger.info('Start Searching Queue Info')
    queue_name = args[0]
    target_url = TARGET_URL + '/' + queue_name
    logger.info(target_url)
    page = requests.get(target_url, auth=HTTPBasicAuth('hourong', '1220'))
    content = page.text
    j_data = json.loads(content)
    # each = list(filter(lambda x: queue_name == x['name'], j_data))[0]
    count = j_data.get('messages_ready')
    max_count = j_data.get('messages_unacknowledged')
    message_count = int(count)
    max_message_count = int(max_count)
    queue_min_task, insert_task_count, _time = TASK_CONF.get(queue_name, TASK_CONF['default'])
    if message_count <= queue_min_task and max_message_count <= queue_min_task \
            and message_count <= QUEUE_MAX_COUNT and max_message_count <= QUEUE_MAX_COUNT:
        logger.warning('Queue {0} insert task, max {1}'.format(queue_name, insert_task_count))
        insert_task(queue_name, insert_task_count)
    else:
        logger.warning('NOW {0} COUNT {1}'.format(queue_name, message_count))


for queue_name, (_min, _max, seconds) in TASK_CONF.items():
    schedule.add_job(mongo_task_watcher, 'cron', args=[queue_name], second='*/' + str(seconds),
                     id=queue_name + '_queue')

if __name__ == '__main__':
    schedule.start()
