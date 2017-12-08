#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/15 下午11:05
# @Author  : Hou Rong
# @Site    : 
# @File    : mongo_task_func.py
# @Software: PyCharm
import pymongo
import datetime
import time
from proj.my_lib.logger import get_logger, func_time_logger
from collections import defaultdict
from proj.my_lib.Common.Task import Task, TaskType

logger = get_logger("mongo_task_func")

client = pymongo.MongoClient(host='10.10.231.105')
db = client['MongoTask']

cursor_dict = {}

MIN_PRIORITY = 0
EACH_UPDATE = 50000


class StopException(Exception):
    pass


def generate_collection_name(queue, task_name):
    return "Task_Queue_{}_TaskName_{}".format(queue, task_name)


@func_time_logger
def get_task_total_simple(queue, used_times=6, limit=30000, debug=False):
    """
    简单从 mongodb 中获取任务的方法
    :type queue: str
    :type used_times: int
    :type limit: int
    :type debug: bool
    :return: Task
    """
    # type:  (str, int, int, bool) -> Task

    collection_prefix = 'Task_Queue_{}_TaskName_'.format(queue)
    c_list = list(filter(lambda x: str(x).startswith(collection_prefix), db.collection_names()))

    if queue == 'poi_list':
        c_list = list(filter(lambda x: str(x).split('_')[-1] >= "20171208b", c_list))

    # 防止过度均分，选取 2000 为最小分配值
    per_limit = max(limit // len(c_list), 2000)
    c_list = list(map(lambda x: (x, per_limit), c_list))

    # if queue == 'file_downloader':
    #     c_list.append(('Task_Queue_file_downloader_TaskName_images_total_qyer_20171201a', 2000))
    #     c_list.append(('Task_Queue_file_downloader_TaskName_images_total_qyer_20171120a', 2000))
    # todo 先均分任务，之后考虑不同的阀值分配不同的任务
    for each_collection_name, each_limit in c_list:
        for d in _get_task_total_simple(collection_name=each_collection_name, queue=queue, used_times=used_times,
                                        limit=each_limit,
                                        debug=debug):
            # _queue, _worker, _task_id, _source, _type, _task_name, _used_times, max_retry_times,
            t_list = d['task_name'].split('_')
            if not t_list:
                continue
            if t_list[0] == 'list':
                task_type = TaskType.LIST_TASK
            else:
                task_type = TaskType.NORMAL

            _task = Task(
                _queue=d['queue'],
                _routine_key=d['routing_key'],
                _worker=d['worker'],
                _task_id=d['task_token'],
                _source=d['source'],
                _type=d['type'],
                _task_name=d['task_name'],
                _used_times=d['used_times'],
                max_retry_times=used_times,
                task_type=task_type,
                list_task_token=d.get('list_task_token', None),
                kwargs=d['args'],
                collection=each_collection_name
            )
            if task_type == TaskType.LIST_TASK:
                _task.list_task_token = d['list_task_token']

            yield _task


@func_time_logger
def _get_task_total_simple(collection_name, queue, used_times=6, limit=10000, debug=False):
    """
    自任务简单逻辑
    :param collection_name:
    :param queue:
    :param used_times:
    :param limit:
    :param debug:
    :return:
    """
    # type: (str, str, int, int, bool) -> dict

    collections = db[collection_name]
    _count = limit
    _total = defaultdict(int)
    _id_list = []
    now = datetime.datetime.now()
    try:
        for each_priority in range(11, MIN_PRIORITY, -1):
            for each_used_times in range(0, used_times + 1):
                cursor = collections.find(
                    {
                        'queue': queue,
                        'finished': 0,
                        # 'used_times': {'$lte': each_used_times},
                        'used_times': each_used_times,
                        'priority': each_priority,
                        'running': 0
                    },
                    hint=[('queue', 1), ('finished', 1), ('used_times', 1), ('priority', 1), ('running', 1)]
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
                    yield line
    except StopException:
        logger.debug("[end of search][queue: {}][num: {}]".format(queue, _total))
    finally:
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


@func_time_logger
def update_task(queue, task_name, task_id, finish_code=0):
    collections = db[generate_collection_name(queue=queue, task_name=task_name)]
    if int(finish_code) == 1:
        return collections.update({
            'task_token': task_id
        }, {
            '$set': {
                "finished": 1,
                'running': 0
            }
        }, multi=True)
    else:
        return collections.update({
            'task_token': task_id
        }, {
            '$set': {
                'running': 0
            }
        }, multi=True)


@func_time_logger
def update_city_list_task(city_collection_name, list_task_token, data_count, task_result):
    """
    通过列表页城市反馈信息更新城市页任务
    :param city_collection_name:
    :param list_task_token:
    :param data_count:
    :param task_result:
    :return:
    """
    # type: (str, str, tuple(str, int, int, bool), bool) -> bool
    city_collections = db[city_collection_name]
    _res = city_collections.find_and_modify(
        query={
            'list_task_token': list_task_token
        },
        update={
            '$push': {
                'data_count': data_count,
                'task_result': task_result
            }
        }
    )
    return bool(_res)


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
    # for line in get_task_total_simple('merge_task', debug=True, limit=20):
    #     pass

    update_city_list_task("City_Queue_poi_list_TaskName_city_total_qyer_20171120a", "e50ff0261cbd53c8d3e6872a71aa3a97",
                          500, True)
