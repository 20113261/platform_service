#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/24 下午5:41
# @Author  : Hou Rong
# @Site    : 
# @File    : routine_task_func.py
# @Software: PyCharm
import pymongo
import datetime

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['MongoTask']['RoutineTask']
failed_routine_task_collections = client['MongoTask']['RoutineFailedTask']
task_collections = client['MongoTask']['Task']


# failed_task_collections = client['MongoTask']['RoutineFailedTask']


def get_routine_task_total(queue, limit=30000):
    for line in collections.find(
            {
                'queue': queue,
                'running': 0
            },
            {
                'result': 0
            }
    ).sort([('priority', -1), ('finished', 1), ('utime', 1)]).limit(limit):
        task_token = line['task_token']
        worker = line['worker']
        routing_key = line['routing_key']
        collections.update({
            'task_token': task_token
        }, {
            '$set': {
                'utime': datetime.datetime.now(),
                'running': 1
            }
        })
        yield task_token, worker, queue, routing_key, line['args']


def update_task(task_id, finished=False):
    if finished:
        return collections.update({
            'task_token': task_id
        }, {
            '$set': {
                'running': 0,
                'finished': 1
            }
        })
    else:
        return collections.update({
            'task_token': task_id
        }, {
            '$set': {
                'running': 0,
            }
        })


def get_per_task(task_id):
    return collections.find_one({'task_token': task_id})


def insert_failed_task(task_id, celery_task_id, args, kwargs, einfo, source, s_type, error_code,
                       is_routine_task=True):
    return True
    try:
        if is_routine_task:
            failed_routine_task_collections.save({
                'task_id': task_id,
                'source': source,
                'type': s_type,
                'error_code': error_code,
                'celery_task_id': celery_task_id,
                'args': args,
                'kwargs': kwargs,
                'einfo': einfo,
            })

        if not is_routine_task:
            task_collections.update(
                {"task_token": task_id},
                {
                    "$push": {
                        "result": {
                            "$each": [
                                {
                                    "error_code": error_code,
                                    "celery_task_id": celery_task_id,
                                    "error_info": einfo,
                                    "datetime": datetime.datetime.now()
                                }
                            ],
                            "$sort": {"datetime": -1},
                            "$slice": 6
                        }
                    }
                }
            )
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
    for each in get_routine_task_total('hotel_task', 10):
        print each
