#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/17 上午11:58
# @Author  : Hou Rong
# @Site    : 
# @File    : MongoTaskInsert.py
# @Software: PyCharm
import mock
import datetime
import pymongo
import logging
import patched_mongo_insert
from toolbox.Hash import get_token
from proj.my_lib.logger import get_logger

spider_data_base_data_config = {
    'host': '10.10.228.253',
    'user': 'mioji_admin',
    'password': 'mioji1109',
    'charset': 'utf8',
    'db': 'base_data'
}

# 当 task 数积攒到每多少时进行一次插入
# 当程序退出后也会执行一次插入，无论当前 task 积攒为多少

INSERT_WHEN = 2000


class Task(object):
    def __init__(self, worker, source, _type, _args, task_name, routine_key, queue, **kwargs):
        self.worker = worker
        self.source = source
        self.type = _type
        self.args = _args
        self.task_name = task_name
        self.routine_key = routine_key
        self.queue = queue

        self.priority = int(kwargs.get("priority", 3))
        self.finished = 0
        self.used_times = 0
        self.running = 0
        self.utime = datetime.datetime.now()
        self.id = self.get_task_id()

    def get_task_id(self):
        return get_token(self.args)

    def to_dict(self):
        return {
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


class TaskList(list):
    def append_task(self, task: Task):
        self.append(task.to_dict())


class InsertTask(object):
    def __init__(self, worker, source, _type, task_name, routine_key, queue, **kwargs):
        self.worker = worker
        self.source = source
        self.type = _type
        self.task_name = task_name
        self.routine_key = routine_key
        self.queue = queue

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
        return "Task_Queue_{}_TaskName_{}".format(self.queue, self.task_name)

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
        collections.create_index([('task_token', 1)], unique=True)
        collections.create_index([('utime', 1)])
        collections.create_index([('finished', 1)])
        self.logger.info("[完成索引建立]")

    def mongo_patched_insert(self, data):
        collections = self.db[self.collection_name]
        with mock.patch('pymongo.collection.Collection._insert', patched_mongo_insert.Collection._insert):
            result = collections.insert(data, continue_on_error=True)
            return result

    def insert_mongo(self):
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

    def _insert_task(self, args):
        if isinstance(args, dict):
            __t = Task(worker=self.worker, source=self.source, _type=self.type, task_name=self.task_name,
                       routine_key=self.routine_key,
                       queue=self.queue, _args=args)
            self.tasks.append_task(__t)
            self.pre_offset += 1

            # 如果当前可以入库，则执行入库
            if self.insert_stat():
                self.insert_mongo()
        else:
            raise TypeError('错误的 args 类型 < {0} >'.format(type(args).__name__))

    def insert_task(self):
        for args in self.get_task():
            self._insert_task(args)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.insert_mongo()
