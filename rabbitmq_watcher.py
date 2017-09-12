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

schedule = BlockingScheduler()

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
    'celery': (9000, 50000),
    'file_downloader': (9000, 20000),
    'full_site_task': (9000, 50000),
    'hotel_list_task': (9000, 50000),
    'hotel_suggestion': (9000, 50000),
    'hotel_task': (9000, 50000),
    'tripadvisor_list_tasks': (9000, 50000),
    'tripadvisor_website': (9000, 50000),
    'poi_task_1': (9000, 50000),
    'poi_task_2': (9000, 50000)
}


def insert_task(queue, limit):
    _count = 0
    for task_token, worker, queue, routing_key, args in get_task_total(queue=queue, limit=limit):
        _count += 1
        kwargs = {
            'mongo_task_id': task_token
        }
        kwargs.update(args)
        app.send_task(
            worker,
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
            kwargs=kwargs,
            queue=queue,
            routing_key=routing_key
        )

    logger.info("Insert queue: {0} Routine task count: {1}".format(queue, _count - emergency_count))
    logger.info("Insert queue: {0} Total task count: {1}".format(queue, _count))


@schedule.scheduled_job('cron', second='*/60')
def mongo_task_watcher():
    logger.info('Start Searching Queue Info')
    target_url = 'http://10.10.189.213:15672/api/queues/celery'
    page = requests.get(target_url, auth=HTTPBasicAuth('hourong', '1220'))
    content = page.text
    j_data = json.loads(content)

    # celery message bool
    for each in list(filter(lambda x: 'celery@' not in x['name'] and 'celeryev' not in x['name'], j_data)):
        queue_name = each['name']
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
