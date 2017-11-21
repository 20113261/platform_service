#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/15 上午10:15
# @Author  : Hou Rong
# @Site    : 
# @File    : Task.py
# @Software: PyCharm
import json


class TaskType(object):
    NORMAL = 0
    LIST_TASK = 1
    CITY_TASK = 2


class Task(object):
    def __init__(self, _queue, _routine_key, _worker, _task_id, _source, _type, _task_name, _used_times,
                 max_retry_times, **kwargs):
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
        self.task_type = kwargs.get('task_type', TaskType.NORMAL)
        self.list_task_token = kwargs.get('list_task_token', None)

        # 初始化任务执行信息
        self.used_times = _used_times,
        self.max_retry_times = max_retry_times

        # 初始化错误码
        self.__error_code = 103

        # 初始化请求参数
        self.kwargs = kwargs

    @property
    def error_code(self):
        return self.__error_code

    @error_code.setter
    def error_code(self, val):
        self.__error_code = int(val)

    def __str__(self):
        return json.dumps(self.__dict__, ensure_ascii=False)
