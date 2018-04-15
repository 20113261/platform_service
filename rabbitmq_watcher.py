#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/6 下午9:01
# @Author  : Hou Rong
# @Site    :
# @File    : rabbitmq_watcher.py
# @Software: PyCharm
import sys
import subprocess

sys.path.append('/root/data/lib')
import json
import requests
import re
from proj.my_lib.logger import get_logger
from apscheduler.schedulers.blocking import BlockingScheduler
from requests.auth import HTTPBasicAuth
from proj.celery import app
from proj.my_lib.task_module.mongo_task_func import get_task_total_simple, quick_task_slow_task_count
from proj.my_lib.task_module.routine_task_func import get_routine_task_total
from monitor import monitoring_hotel_detail2ImgOrComment, monitoring_hotel_list2detail, \
    monitoring_poi_detail2imgOrComment, monitoring_poi_list2detail, monitoring_qyer_list2detail, \
    monitoring_supplement_field, monitoring_zombies_task_by_hour, city2list, monitoring_zombies_task_total, \
    monitoring_ctripPoi_list2detail, monitoring_GT_list2detail ,monitoring_PoiSource_list2detail, \
    monitoring_result_list2detail, monitoring_result_daodao_filter
from proj.config import BROKER_URL
from proj.my_lib.Common.Task import Task
from rabbitmq_func import detect_msg_num

schedule = BlockingScheduler()

hotel_slow_source = {
    'ihg':
        {
            'proj.total_tasks.hotel_detail_task': (
                'proj.total_tasks.slow_hotel_detail_task',
                'slow_hotel_detail',
                'slow_hotel_detail'
            ),
            'proj.total_tasks.hotel_list_task': (
                'proj.total_tasks.slow_hotel_list_task',
                'slow_hotel_list',
                'slow_hotel_list'
            )
        },
    'holiday':
        {
            'proj.total_tasks.hotel_detail_task': (
                'proj.total_tasks.slow_hotel_detail_task',
                'slow_hotel_detail',
                'slow_hotel_detail'
            ),
            'proj.total_tasks.hotel_list_task': (
                'proj.total_tasks.slow_hotel_list_task',
                'slow_hotel_list',
                'slow_hotel_list'
            )
        },
    'accor':
        {
            'proj.total_tasks.hotel_detail_task': (
                'proj.total_tasks.slow_hotel_detail_task',
                'slow_hotel_detail',
                'slow_hotel_detail'
            ),
            'proj.total_tasks.hotel_list_task': (
                'proj.total_tasks.slow_hotel_list_task',
                'slow_hotel_list',
                'slow_hotel_list'
            )
        },
    'marriott':
        {
            'proj.total_tasks.hotel_detail_task': (
                'proj.total_tasks.slow_hotel_detail_task',
                'slow_hotel_detail',
                'slow_hotel_detail'
            ),
            'proj.total_tasks.hotel_list_task': (
                'proj.total_tasks.slow_hotel_list_task',
                'slow_hotel_list',
                'slow_hotel_list'
            )
        }
}

slow_source = 'ihg|holiday|accor|marriott'

import datetime


def restart_slave_temp():
    logger.info('开始')
    try:
        p = subprocess.Popen("pssh -h /root/hosts.txt -i 'service supervisord restart'", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        while 1:
            if p.poll() is not None:
                stdout = p.stdout.read()
                logger.info(stdout)
                break
    except:pass
    logger.info('开始2')
    p2 = subprocess.Popen("pssh -h /root/hosts.txt -i 'service supervisord restart'", stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    while 1:
        if p2.poll() is not None:
            stdout2 = p2.stdout.read()
            logger.info(stdout2)
            break

    logger.info('结束')

# schedule.add_job(restart_slave_temp, 'cron', minute='*/6', id='restart_slave_temp')

# schedule.add_job(restart_slave_temp, 'date', next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=10), id='monitoring_hotel_list')
schedule.add_job(monitoring_hotel_list2detail, 'cron', second='*/45',
                 next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=50), id='monitoring_hotel_list')
schedule.add_job(monitoring_result_list2detail, 'cron', second='*/47',
                 next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=50), id='monitoring_result_list2detail')
schedule.add_job(monitoring_result_daodao_filter, 'cron', second='*/41',
                 next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=50), id='monitoring_result_daodao_filter')
schedule.add_job(monitoring_hotel_detail2ImgOrComment, 'cron', second='*/31',
                 next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=150), id='monitoring_hotel_detail')
schedule.add_job(monitoring_poi_list2detail, 'cron', second='*/45',
                 next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=25), id='monitoring_poi_list')
schedule.add_job(monitoring_poi_detail2imgOrComment, 'cron', second='*/33', id='monitoring_poi_detail')
schedule.add_job(monitoring_qyer_list2detail, 'cron', second='*/45',
                 next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=2), id='monitoring_qyer_detail')
schedule.add_job(monitoring_supplement_field, 'cron', hour='*/2',
                 next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=7),
                 id='monitoring_supplement_field')
# schedule.add_job(monitoring_ctripPoi_list2detail, 'cron', second='*/45',
#                  next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=50), id='monitoring_ctripPoi_list')

schedule.add_job(monitoring_GT_list2detail, 'cron', second='*/45',
                 next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=50), id='monitoring_ctripGT_list')
schedule.add_job(monitoring_PoiSource_list2detail, 'cron', second='*/45',
                 next_run_time=datetime.datetime.now() + datetime.timedelta(seconds=50), id='monitoring_PoiSource_list')
schedule.add_job(city2list, 'cron', second='*/59', id='city2list')
schedule.add_job(monitoring_zombies_task_by_hour, 'cron', second='*/59', id='monitoring_zombies_task_by_hour')
schedule.add_job(monitoring_zombies_task_total, 'cron', second='*/59', id='monitoring_zombies_task_total')


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
    'file_downloader': (2000, 3000, 10),
    'hotel_detail': (3200, 5000, 10),
    'hotel_list': (3200, 5000, 10),
    'poi_detail': (36000, 40000, 10),
    'poi_list': (36000, 40000, 10),
    'supplement_field': (9000, 40000, 10),
    'google_api': (9000, 40000, 10),
    'merge_task': (10000, 40000, 11),
    'grouptravel': (4600, 6000, 2)
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
        # 初始化需要修改的 worker
        changed_worker = None
        if task.source.lower() in hotel_slow_source:
            s = task.source.lower()
            change_worker_dict = hotel_slow_source[s]
            if task.worker in change_worker_dict:
                changed_worker, changed_queue, changed_routine_key = change_worker_dict[task.worker]
        if changed_worker is None:
            app.send_task(
                task.worker,
                task_id="[collection: {}][tid: {}]".format(task.collection, task.task_id),
                kwargs={'task': task},
                queue=task.queue,
                routing_key=task.routine_key
            )
        else:
            # 如果需要开启慢任务
            app.send_task(
                changed_worker,
                task_id="[collection: {}][tid: {}]".format(task.collection, task.task_id),
                kwargs={'task': task},
                queue=changed_queue,
                routing_key=changed_routine_key
            )
    logger.info("Insert queue: {0} task count: {1}".format(queue, _count))


def mongo_task_watcher(*args):
    logger.info('Start Searching Queue Info')
    queue_name = args[0]

    idle_seconds, message_count, max_message_count = detect_msg_num(queue_name=queue_name)

    if queue_name == 'hotel_list':
        slow_idle_seconds, slow_message_count, slow_max_message_count = detect_msg_num(queue_name='slow_hotel_list')

    elif queue_name == 'hotel_detail':
        slow_idle_seconds, slow_message_count, slow_max_message_count = detect_msg_num(queue_name='slow_hotel_detail')
    else:
        slow_idle_seconds, slow_message_count, slow_max_message_count = 0, 0, 0

    queue_min_task, insert_task_count, _time = TASK_CONF.get(queue_name, TASK_CONF['default'])

    task_count = quick_task_slow_task_count(queue=queue_name, slow_source=slow_source, limit=insert_task_count)

    if (message_count + slow_message_count) > queue_min_task \
            or (max_message_count + slow_max_message_count) > queue_min_task \
            or (message_count + slow_message_count) > QUEUE_MAX_COUNT \
            or (max_message_count + slow_max_message_count) > QUEUE_MAX_COUNT:
        pass
    elif task_count[True] > 0 and message_count <= queue_min_task and max_message_count <= queue_min_task \
            and message_count <= QUEUE_MAX_COUNT and max_message_count <= QUEUE_MAX_COUNT:
        logger.warning('Queue {0} insert task, max {1}'.format(queue_name, insert_task_count))
        insert_task(queue_name, insert_task_count)
    elif task_count[False] > 0 and slow_message_count <= queue_min_task and slow_max_message_count <= queue_min_task \
            and slow_message_count <= QUEUE_MAX_COUNT and slow_max_message_count <= QUEUE_MAX_COUNT:
        insert_task(queue_name, insert_task_count)
    else:
        logger.warning('NOW {0} COUNT {1}'.format(queue_name, message_count))


for queue_name, (_min, _max, seconds) in TASK_CONF.items():
    schedule.add_job(mongo_task_watcher, 'cron', args=[queue_name], second='*/' + str(seconds),
                     id=queue_name + '_queue')

if __name__ == '__main__':
    schedule.start()
    #insert_task('poi_list', limit=10000)

