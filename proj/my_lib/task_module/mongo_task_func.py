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
from collections import defaultdict

logger = get_logger("mongo_task_func")

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['MongoTask']['Task']
failed_task_collections = client['MongoTask']['FailedTask']

cursor_dict = {}

MIN_PRIORITY = 1
EACH_UPDATE = 1000


class StopException(Exception):
    pass


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
def get_task_total_simple(queue, used_times=6, limit=30000, debug=False):
    _count = limit
    _total = defaultdict(int)
    _id_list = []
    now = datetime.datetime.now()
    try:
        for each_priority in range(10, MIN_PRIORITY, -1):
            for each_used_times in range(0, used_times + 1):
                cursor = collections.find(
                    {
                        'finished': 0,
                        'queue': queue,
                        # 'used_times': {'$lte': each_used_times},
                        'used_times': each_used_times,
                        'priority': each_priority,
                        'running': 0
                    }
                ).limit(_count)
                logger.debug(
                    '[queue: {}][priority: {}][used_times: {}][limit: {}][debug: {}]'.format(queue, each_priority,
                                                                                             each_used_times, _count,
                                                                                             debug))

                for line in cursor:
                    _total[(each_priority, each_used_times)] += 1
                    _count -= 1

                    if _count == 0:
                        raise StopException()
                    task_token = line['task_token']
                    worker = line['worker']
                    routing_key = line['routing_key']

                    if not debug:
                        if len(_id_list) == EACH_UPDATE:
                            collections.update({
                                '_id': {
                                    '$in': _id_list
                                }
                            }, {
                                '$set': {
                                    'utime': now,
                                    'running': 1
                                },
                                '$inc': {'used_times': 1}
                            }, multi=True)
                            _id_list = []
                    else:
                        if len(_id_list) == 5:
                            for i in collections.find({
                                '_id': {
                                    '$in': _id_list
                                }
                            }):
                                logger.debug(i['_id'])
                                logger.debug(i)
                            _id_list = []
                    _id_list.append(line['_id'])
                    yield task_token, worker, queue, routing_key, line['args'], line['used_times'], line['task_name']

        if not debug:
            collections.update({
                '_id': {
                    '$in': _id_list
                }
            }, {
                '$set': {
                    'utime': now,
                    'running': 1
                },
                '$inc': {'used_times': 1}
            }, multi=True)
        else:
            for i in collections.find({
                '_id': {
                    '$in': _id_list
                }
            }):
                logger.debug(i['_id'])
                logger.debug(i)
    except StopException:
        logger.debug("[end of search][queue: {}][num: {}]".format(queue, _total))


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

    logger.debug('[queue: {}][mongo task cursor: {}][cursor mem id: {}]'.format(queue, cursor.cursor_id, id(cursor)))
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
    for line in get_task_total_simple('file_downloader', debug=True, limit=20):
        pass
