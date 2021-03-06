#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/15 上午10:15
# @Author  : Hou Rong
# @Site    : 
# @File    : Task.py
# @Software: PyCharm
import json


class TaskStatus(object):
    READY = 0
    FINISHED = 1
    FAILED = 2


class TaskType(object):
    NORMAL = 0
    LIST_TASK = 1
    CITY_TASK = 2


class Task(object):
    def __init__(self, _queue, _routine_key, _worker, _task_id, _source, _type, _task_name, _used_times,
                 max_retry_times, task_type, list_task_token, kwargs, collection='Unknown'):
        """
        抓取平台任务对象
        :param _queue:
        :param _routine_key:
        :param _worker:
        :param _task_id:
        :param _source:
        :param _type:
        :param _task_name:
        :param _used_times:
        :param max_retry_times:
        :param task_type:
        :param list_task_token:
        :param collection:
        :type kwargs: dict
        """
        # 初始化任务信息
        self.queue = _queue
        self.routine_key = _routine_key
        self.worker = _worker
        self.task_id = _task_id
        self.source = _source
        self.type = _type
        self.task_name = _task_name
        self.task_type = task_type
        self.list_task_token = list_task_token

        # 初始化任务执行信息
        self.used_times = _used_times,
        self.max_retry_times = max_retry_times

        # 初始化错误码
        self.__error_code = 103

        # 初始化请求参数
        self.kwargs = kwargs

        # 初始化任务状态
        self.status = TaskStatus.READY
        self.task_finished_code = [0, ]

        # 列表页任务特殊变量
        self.__list_task_insert_db_count = 0
        self.__get_data_per_times = 0

        # 任务 collection 信息
        self.collection = collection

    @property
    def list_task_insert_db_count(self):
        return self.__list_task_insert_db_count

    @list_task_insert_db_count.setter
    def list_task_insert_db_count(self, val):
        if not val:
            res = 0
        else:
            res = int(val)
        self.__list_task_insert_db_count = res

    @property
    def get_data_per_times(self):
        return self.__get_data_per_times

    @get_data_per_times.setter
    def get_data_per_times(self, val):
        if not val:
            res = 0
        else:
            res = int(val)
        self.__get_data_per_times = res

    @property
    def error_code(self):
        return self.__error_code

    @error_code.setter
    def error_code(self, val):
        self.__error_code = int(val)
        self.update_task_status()

    def update_task_status(self):
        if self.error_code in self.task_finished_code:
            self.status = TaskStatus.FINISHED
        else:
            self.status = TaskStatus.FAILED

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)
