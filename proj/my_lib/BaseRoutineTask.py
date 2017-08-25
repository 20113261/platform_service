#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/10 上午9:14
# @Author  : Hou Rong
# @Site    : 
# @File    : BaseRoutineTask.py
# @Software: PyCharm
# coding=utf-8
import redis
import time
import types
from celery.app.log import get_logger
from celery.task import Task

from proj.my_lib.Common.Utils import get_local_ip
from proj.my_lib.task_module.routine_task_func import insert_failed_task, update_task

logger = get_logger(__name__)

FAILED_TASK_BLACK_LIST = {'proj.full_website_spider_task.full_site_spider'}


def get_str_type_object_attribute(obj, attr_name):
    if hasattr(obj, attr_name):
        attr_obj = getattr(obj, attr_name)
        if isinstance(attr_obj, types.StringTypes):
            return attr_obj
    return 'NULL'


def get_source(obj):
    return get_str_type_object_attribute(obj, 'task_source')


def get_type(obj):
    return get_str_type_object_attribute(obj, 'task_type')


def get_error_code(obj):
    return get_str_type_object_attribute(obj, 'error_code')


class BaseRoutineTask(Task):
    default_retry_delay = 1
    max_retries = 3

    def on_success(self, retval, task_id, args, kwargs):
        # 增加源以及抓取类型统计
        task_source = get_source(self)
        task_type = get_type(self)
        r = redis.Redis(host='10.10.180.145', db=15)
        error_code = get_error_code(self)
        update_task(kwargs['mongo_task_id'])
        r.incr('|_||_|'.join([self.name, get_local_ip(), task_source, task_type, error_code, 'success']))

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        task_source = get_source(self)
        task_type = get_type(self)
        r = redis.Redis(host='10.10.180.145', db=15)
        error_code = get_error_code(self)
        update_task(kwargs['mongo_task_id'])
        r.incr('|_||_|'.join([self.name, get_local_ip(), task_source, task_type, error_code, 'failure']))

        # insert exc into failed task
        celery_task_id = task_id
        task_id = kwargs.get('mongo_task_id', '')
        kwargs.pop('mongo_task_id', None)
        kwargs['local_ip'] = get_local_ip()
        kwargs['u-time'] = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())
        insert_failed_task(task_id, celery_task_id, args, kwargs, str(einfo))


if __name__ == '__main__':
    pass
