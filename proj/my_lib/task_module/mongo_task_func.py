#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/15 下午11:05
# @Author  : Hou Rong
# @Site    : 
# @File    : mongo_task_func.py
# @Software: PyCharm
import pymongo
import datetime
from proj.my_lib.logger import get_logger, func_time_logger

logger = get_logger("mongo_task_func")

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['MongoTask']['Task']
failed_task_collections = client['MongoTask']['FailedTask']

cursor_dict = {}


def init_cursor(queue, used_times):
    cursor = collections.find(
        {
            'finished': 0,
            'queue': queue,
            'used_times': {'$lte': used_times},
            'running': 0
        }
    )
    # ).sort([('priority', -1), ('used_times', 1), ('utime', 1)])
    return cursor


@func_time_logger
def get_task_total_iter(queue, used_times=6, limit=30000, debug=False):
    # init cursor
    global cursor_dict
    cursor = cursor_dict.get(queue, None)
    if cursor is None:
        cursor = init_cursor(queue=queue, used_times=used_times)
        cursor_dict[queue] = cursor
    # init now time
    now = datetime.datetime.now()

    _count = 0
    while True:
        if _count == limit:
            break
        _count += 1

        # get per line
        try:
            line = cursor.next()
        except StopIteration:
            # end of iter break
            break

        task_token = line['task_token']
        worker = line['worker']
        routing_key = line['routing_key']

        if not debug:
            collections.update({
                'task_token': task_token
            }, {
                '$set': {
                    'utime': now,
                    'running': 1
                },
                '$inc': {'used_times': 1}
            })
        yield task_token, worker, queue, routing_key, line['args'], line['used_times'], line['task_name']


@func_time_logger
def get_task_total(queue, used_times=6, limit=30000):
    now = datetime.datetime.now()
    for line in collections.find(
            {
                'finished': 0,
                'queue': queue,
                # 'used_times': {'$lte': used_times},
                'running': 0
            }
    ).sort([('priority', -1), ('used_times', 1), ('utime', 1)]).limit(limit):
        task_token = line['task_token']
        worker = line['worker']
        routing_key = line['routing_key']
        collections.update({
            'task_token': task_token
        }, {
            '$set': {
                'utime': now,
                'running': 1
            },
            '$inc': {'used_times': 1}
        })
        yield task_token, worker, queue, routing_key, line['args'], line['used_times'], line['task_name']


@func_time_logger
def update_task(task_id, finish_code=0):
    if int(finish_code) == 1:
        return collections.update({
            'task_token': task_id
        }, {
            '$set': {
                "finished": 1,
                'running': 0
            }
        })
    else:
        return collections.update({
            'task_token': task_id
        }, {
            '$set': {
                'running': 0
            }
        })


@func_time_logger
def get_per_task(task_id):
    return collections.find_one({'task_token': task_id})


@func_time_logger
def insert_failed_task(task_id, celery_task_id, args, kwargs, einfo):
    try:
        failed_task_collections.save({
            'task_id': task_id,
            'celery_task_id': celery_task_id,
            'args': args,
            'kwargs': kwargs,
            'einfo': einfo,
        })
    except Exception:
        pass


if __name__ == '__main__':
    # for line in get_task_total(10):
    #     print line
    # print update_task('537019182ea35ad39e8223f534f6cdd3')
    # print get_per_task('596a3208e28b5414c164c3b1')
    # print get_per_task('537019182ea35ad39e8223f534f6cdd3')
    # for each in get_task_total('test'):
    #     print each

    # count = 0
    # for each in get_task_total('file_downloader', limit=50000):
    #     count += 1
    #
    # print count
    # for each in get_task_total('poi_detail', used_times=6, limit=30000):
    #     print(each)
    # {"task_name": "detail_rest_daodao_20170925a", "finished": 1}
    pass
