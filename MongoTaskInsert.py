#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/17 上午11:58
# @Author  : Hou Rong
# @Site    : 
# @File    : MongoTaskInsert.py
# @Software: PyCharm
import mock
import copy
import datetime
import pymongo
import logging
import functools
import toolbox.Date
import patched_mongo_insert
from toolbox.Hash import get_token
from proj.my_lib.logger import get_logger
from toolbox.Date import date_takes

# 配置 toolbox 日期格式

toolbox.Date.DATE_FORMAT = "%Y%m%d"

# 当 task 数积攒到每多少时进行一次插入
# 当程序退出后也会执行一次插入，无论当前 task 积攒为多少

INSERT_WHEN = 2000


class TaskType(object):
    NORMAL = 0
    LIST_TASK = 1
    CITY_TASK = 2


class Task(object):
    def __init__(self, worker, source, _type, _args, task_name, routine_key, queue, **kwargs):
        self.worker = worker
        self.source = source
        self.type = _type
        self.args = _args
        self.task_name = task_name
        self.routine_key = routine_key
        self.queue = queue

        # 任务类型
        self.task_type = kwargs.get('task_type', TaskType.NORMAL)

        self.priority = int(kwargs.get("priority", 3))
        self.finished = 0
        self.used_times = 0
        self.running = 0
        self.utime = datetime.datetime.now()
        self.id = self.get_task_id()

        # 任何任务都获得 list_task_token 默认与 task_token 相同，只有 list 中不同
        self.list_task_token = self.get_task_id(list_task_token=True)
        # city task 专属添加值
        self.date_list = kwargs.get("date_list", None)

    def get_task_id(self, list_task_token=False):
        if not list_task_token:
            return get_token(self.args)
        else:
            c_args = copy.copy(self.args)
            if 'check_in' in c_args:
                c_args.pop('check_in')
            return get_token(c_args)

    def to_dict(self):
        if self.task_type in (TaskType.NORMAL, TaskType.LIST_TASK):
            task_dict = {
                'task_token': self.id,
                'worker': self.worker,
                'queue': self.queue,
                'routing_key': self.routine_key,
                'task_name': self.task_name,
                'source': self.source,
                'type': self.type,
                'args': self.args,
                'priority': self.priority,
                'running': self.running,
                'used_times': self.used_times,
                'finished': self.finished,
                'utime': self.utime
            }
            if self.task_type == TaskType.LIST_TASK:
                # 针对列表页 task 添加列表页 task_token
                task_dict['list_task_token'] = self.list_task_token
        elif self.task_type == TaskType.CITY_TASK:
            task_dict = {
                'list_task_token': self.list_task_token,
                # 数据新增数目
                'data_count': [],
                # 本次任务 成功 / 失败
                'task_result': [],
                # 当前使用的时间序列
                'date_list': self.date_list,
                # 当前最大使用的日期
                'date_index': 0,
                # 其他参数
                'worker': self.worker,
                'queue': self.queue,
                'routing_key': self.routine_key,
                'task_name': self.task_name,
                'source': self.source,
                'type': self.type,
                'args': self.args,
                'priority': self.priority,
                'running': self.running,
                'used_times': self.used_times,
                'finished': self.finished,
                'utime': self.utime
            }
        else:
            raise TypeError("Unknown Type: {}".format(self.task_type))

        return task_dict


class TaskList(list):
    def append_task(self, task):
        self.append(task.to_dict())


class InsertTask(object):
    def __init__(self, worker, source, _type, task_name, routine_key, queue, **kwargs):
        # 任务基本信息
        self.worker = worker
        self.source = source
        self.type = _type
        self.task_name = task_name
        self.routine_key = routine_key
        self.queue = queue
        self.task_type = kwargs.get('task_type', TaskType.NORMAL)

        self.priority = int(kwargs.get("priority", 3))
        self.logger = get_logger("InsertMongoTask")
        self.tasks = TaskList()

        self.collection_name = self.generate_collection_name()

        # 数据游标偏移量，用于在查询时发生异常恢复游标位置
        self.offset = 0
        # 数据游标前置偏移量，用于在入库时恢复游标位置
        self.pre_offset = 0

        client = pymongo.MongoClient(host='10.10.231.105')
        self.db = client['MongoTask']

        # 建立所需要的全部索引
        self.create_mongo_indexes()

        # CITY TASK 获取 date_list
        if self.task_type == TaskType.CITY_TASK:
            self.date_list = self.generate_list_date()
        else:
            self.date_list = None

        # 修改 logger 日志打印
        # modify handler's formatter
        datefmt = "%Y-%m-%d %H:%M:%S"
        file_log_format = "%(asctime)-15s %(threadName)s %(filename)s:%(lineno)d %(levelname)s " \
                          "[source: {}][type: {}][task_name: {}][collection_name: {}]:        %(message)s".format(
            self.source, self.type, self.task_name, self.collection_name)
        formtter = logging.Formatter(file_log_format, datefmt)

        for each_handler in self.logger.handlers:
            each_handler.setFormatter(formtter)
        self.logger.info("[init InsertTask]")

    def generate_collection_name(self):
        if self.task_type != TaskType.CITY_TASK:
            return "Task_Queue_{}_TaskName_{}".format(self.queue, self.task_name)
        else:
            return "City_Queue_{}_TaskName_{}".format(self.queue, self.task_name)

    def create_mongo_indexes(self):
        collections = self.db[self.collection_name]
        collections.create_index([('finished', 1)])
        collections.create_index([('priority', -1), ('used_times', 1), ('utime', 1)])
        collections.create_index([('queue', 1), ('finished', 1), ('running', 1)])
        collections.create_index([('queue', 1), ('finished', 1), ('running', 1), ('used_times', 1)])
        collections.create_index([('queue', 1), ('finished', 1), ('used_times', 1), ('priority', 1)])
        collections.create_index(
            [('queue', 1), ('finished', 1), ('used_times', 1), ('priority', 1), ('running', 1)])
        collections.create_index([('running', 1), ('utime', 1)])
        collections.create_index([('running', 1), ('utime', -1)])
        collections.create_index([('task_name', 1)])
        collections.create_index([('task_name', 1), ('finished', 1)])
        collections.create_index([('task_name', 1), ('finished', 1), ('used_times', 1)])
        collections.create_index([('task_name', 1), ('list_task_token', 1)])
        if self.task_type in (TaskType.NORMAL, TaskType.LIST_TASK):
            collections.create_index([('task_token', 1)], unique=True)
        elif self.task_type == TaskType.CITY_TASK:
            collections.create_index([('list_task_token', 1)], unique=True)
        collections.create_index([('utime', 1)])
        collections.create_index([('finished', 1)])
        self.logger.info("[完成索引建立]")

    def generate_list_date(self):
        collection_name = "CityTaskDate"
        collections = self.db[collection_name]
        _res = collections.find_one({
            'task_name': self.task_name
        })
        if not _res:
            dates = list(date_takes(360, 5, 10))
            collections.save({
                'task_name': self.task_name,
                'dates': dates
            })
            self.logger.info("[new date list][task_name: {}][dates: {}]".format(self.task_name, dates))
        else:
            self.logger.info(
                "[date already generate][task_name: {}][dates: {}]".format(_res['task_name'], _res['dates']))
        return _res['_id']

    def mongo_patched_insert(self, data):
        collections = self.db[self.collection_name]
        with mock.patch('pymongo.collection.Collection._insert', patched_mongo_insert.Collection._insert):
            result = collections.insert(data, continue_on_error=True)
            return result

    def insert_mongo(self):
        if len(self.tasks) > 0:
            res = self.mongo_patched_insert(self.tasks)
            self.logger.info("[update offset][offset: {}][pre offset: {}]".format(self.offset, self.pre_offset))
            self.offset = self.pre_offset
            self.logger.info("[insert info][ offset: {} ][ {} ]".format(self.offset, res))
            self.logger.info('[ 本次准备入库任务数：{0} ][ 实际入库数：{1} ][ 库中已有任务：{2} ][ 已完成总数：{3} ]'.format(
                self.tasks.__len__(), res['n'], res.get('err', 0), self.offset))

            # 入库完成，清空任务列表
            self.tasks = TaskList()

    def insert_stat(self):
        """
        用于检查当前是否可以准备将任务入到 mysql 中
        :return: bool 是否准备将任务入到 mysql 中
        """
        return len(self.tasks) >= INSERT_WHEN

    def get_task(self):
        yield

    def insert_task(self, args):
        if isinstance(args, dict):
            __t = Task(worker=self.worker, source=self.source, _type=self.type, task_name=self.task_name,
                       routine_key=self.routine_key,
                       queue=self.queue, task_type=self.task_type, date_list=self.date_list, _args=args)
            self.tasks.append_task(__t)
            self.pre_offset += 1

            # 如果当前可以入库，则执行入库
            if self.insert_stat():
                self.insert_mongo()
        else:
            raise TypeError('错误的 args 类型 < {0} >'.format(type(args).__name__))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.insert_mongo()
