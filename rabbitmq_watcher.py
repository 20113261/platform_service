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
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from requests.auth import HTTPBasicAuth
from proj.celery import app
from proj.my_lib.task_module.mongo_task_func import get_task_total

schedule = BlockingScheduler()

stream_handler = logging.StreamHandler()
logger = logging.getLogger('rabbitmq_watcher')
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)

'''
用于管理分发任务的数目
默认为 default 值
key 任务队列名称 val (队列中最少的任务数，单次插入任务数)
'''
TASK_CONF = {
    'default': (0, 0),
    'celery': (9000, 50000),
    'file_downloader': (9000, 50000),
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
    logger.info("Insert queue: {0} task count: {1}".format(queue, _count))


@schedule.scheduled_job('cron', second='*/10')
def mongo_task_watcher():
    logger.info('Start Searching Queue Info')
    target_url = 'http://10.10.189.213:15672/api/queues/celery'
    page = requests.get(target_url, auth=HTTPBasicAuth('hourong', '1220'))
    content = page.text
    j_data = json.loads(content)

    # celery message bool
    for each in filter(lambda x: 'celery@' not in x['name'] and 'celeryev' not in x['name'], j_data):
        queue_name = each['name']
        message_count = int(each['messages'])
        queue_min_task, insert_task_count = TASK_CONF.get(queue_name, TASK_CONF['default'])
        if message_count <= queue_min_task:
            insert_task(queue_name, insert_task_count)
        else:
            logger.warning('NOW {0} COUNT {1}'.format(queue_name, message_count))


if __name__ == '__main__':
    schedule.start()
    # mongo_task_watcher()
