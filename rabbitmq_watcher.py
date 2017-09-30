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
from proj.my_lib.logger import get_logger
from apscheduler.schedulers.blocking import BlockingScheduler
from requests.auth import HTTPBasicAuth
from proj.celery import app
from proj.my_lib.task_module.mongo_task_func import get_task_total
from proj.my_lib.task_module.routine_task_func import get_routine_task_total
from monitor import monitoring_hotel_detail2ImgOrComment, monitoring_hotel_list2detail, \
    monitoring_poi_detail2imgOrComment, monitoring_poi_list2detail, monitoring_qyer_list2detail

schedule = BlockingScheduler()

import datetime

# schedule.add_job(monitoring_hotel_list2detail, 'date', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=10), id='monitoring_hotel_list')
# schedule.add_job(monitoring_hotel_list2detail, 'cron', second='*/300', id='monitoring_hotel_list')
# schedule.add_job(monitoring_hotel_detail2ImgOrComment, 'cron', second='*/450', id='monitoring_hotel_detail')
# schedule.add_job(monitoring_poi_list2detail, 'cron', second='*/300', id='monitoring_poi_list')
# schedule.add_job(monitoring_poi_detail2imgOrComment, 'cron', second='*/450', id='monitoring_poi_detail')
# schedule.add_job(monitoring_qyer_list2detail, 'cron', second='*/300', id='monitoring_qyer_detail')

# stream_handler = logging.StreamHandler()
# logger = logging.getLogger('rabbitmq_watcher')
# logger.addHandler(stream_handler)
# logger.setLevel(logging.DEBUG)
logger = get_logger("rabbitmq_watcher")
'''
用于管理分发任务的数目
默认为 default 值
key 任务队列名称 val (队列中最少的任务数，单次插入任务数)
'''
TASK_CONF = {
    'default': (0, 0),
    'file_downloader': (1000, 5000),
    'hotel_detail': (18000, 50000),
    'hotel_list': (18000, 50000),
    'poi_detail': (18000, 50000),
    'poi_list': (18000, 50000)
}

MAX_RETRY_TIMES_CONF = {
    'hotel_list_task': 10,
}

DEFAULT_MAX_RETRY_TIMES = 6


def get_max_retry_times(queue_name):
    return MAX_RETRY_TIMES_CONF.get(queue_name, DEFAULT_MAX_RETRY_TIMES)


def insert_task(queue, limit):
    _count = 0
    max_retry_times = get_max_retry_times(queue_name=queue)
    for task_token, worker, queue, routing_key, args, used_times, task_name in get_task_total(queue=queue, limit=limit,
                                                                                              used_times=max_retry_times):
        _count += 1
        kwargs = {
            'mongo_task_id': task_token,
            'retry_count': used_times,
            'max_retry_times': max_retry_times,
            'task_name': task_name
        }
        kwargs.update(args)
        app.send_task(
            worker,
            task_id=task_token,
            kwargs=kwargs,
            queue=queue,
            routing_key=routing_key
        )
    emergency_count = _count
    logger.info("Insert queue: {0} Emergency task count: {1}".format(queue, _count))

    for task_token, worker, queue, routing_key, args in get_routine_task_total(queue=queue, limit=limit - _count):
        _count += 1
        kwargs = {
            'mongo_task_id': task_token
        }
        kwargs.update(args)
        app.send_task(
            worker,
            task_id=task_token,
            kwargs=kwargs,
            queue=queue,
            routing_key=routing_key
        )

    logger.info("Insert queue: {0} Routine task count: {1}".format(queue, _count - emergency_count))
    logger.info("Insert queue: {0} Total task count: {1}".format(queue, _count))


@schedule.scheduled_job('cron', second='*/20')
def mongo_task_watcher():
    logger.info('Start Searching Queue Info')
    target_url = 'http://10.10.189.213:15672/api/queues/celery'
    page = requests.get(target_url, auth=HTTPBasicAuth('hourong', '1220'))
    content = page.text
    j_data = json.loads(content)

    # celery message bool
    for each in list(filter(lambda x: 'celery@' not in x['name'] and 'celeryev' not in x['name'], j_data)):
        queue_name = each['name']
        if queue_name=='file_downloader':continue
        message_count = int(each['messages'])
        queue_min_task, insert_task_count = TASK_CONF.get(queue_name, TASK_CONF['default'])
        if message_count <= queue_min_task:
            logger.warning('Queue {0} insert task, max {1}'.format(queue_name, insert_task_count))
            insert_task(queue_name, insert_task_count)
        else:
            logger.warning('NOW {0} COUNT {1}'.format(queue_name, message_count))


@schedule.scheduled_job('cron', second='*/6', id='file_downloader_queue')
def mongo_task_watcher2():
    logger.info('Start Searching Queue Info')
    target_url = 'http://10.10.189.213:15672/api/queues/celery'
    page = requests.get(target_url, auth=HTTPBasicAuth('hourong', '1220'))
    content = page.text
    j_data = json.loads(content)

    # celery message bool
    for each in list(filter(lambda x: 'celery@' not in x['name'] and 'celeryev' not in x['name'], j_data)):
        queue_name = each['name']
        if queue_name!='file_downloader':continue
        message_count = int(each['messages'])
        queue_min_task, insert_task_count = TASK_CONF.get(queue_name, TASK_CONF['default'])
        if message_count <= queue_min_task:
            logger.warning('Queue {0} insert task, max {1}'.format(queue_name, insert_task_count))
            insert_task(queue_name, insert_task_count)
        else:
            logger.warning('NOW {0} COUNT {1}'.format(queue_name, message_count))


if __name__ == '__main__':
    schedule.start()
    # mongo_task_watcher()
    # insert_task('hotel_task', 100)
