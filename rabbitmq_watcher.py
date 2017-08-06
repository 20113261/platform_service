#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/6 下午9:01
# @Author  : Hou Rong
# @Site    : 
# @File    : rabbitmq_watcher.py
# @Software: PyCharm
import json
import logging
import requests
from apscheduler.schedulers.blocking import BlockingScheduler
from requests.auth import HTTPBasicAuth

schedule = BlockingScheduler()

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


@schedule.scheduled_job('cron', second='*/10')
def mongo_task_watcher():
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
            # todo insert task
            print 'Insert {0} task counts: {1}'.format(queue_name, insert_task_count)
        else:
            logging.warning('NOW {0} COUNT {1}'.format(queue_name, message_count))


if __name__ == '__main__':
    # schedule.start()
    mongo_task_watcher()
