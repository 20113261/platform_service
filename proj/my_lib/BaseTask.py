# coding=utf-8
import pymysql
import json
import redis
import socket
import time
import types
from celery.app.log import get_logger
from celery.task import Task

from proj.my_lib.Common.Utils import get_local_ip
from proj.my_lib.task_module.task_func import update_task
from proj.my_lib.task_module.mongo_task_func import update_task as mongo_update_task, \
    insert_failed_task as mongo_insert_failed_task

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


class BaseTask(Task):
    default_retry_delay = 1
    max_retries = 3

    def on_success(self, retval, task_id, args, kwargs):
        # 增加源以及抓取类型统计
        task_source = get_source(self)
        task_type = get_type(self)
        r = redis.Redis(host='10.10.180.145', db=3)
        r.incr('|_||_|'.join([self.name, get_local_ip(), task_source, task_type, 'success']))
        if 'task_id' in kwargs:
            update_task(kwargs['task_id'])
        if 'mongo_task_id' in kwargs:
            mongo_update_task(kwargs['mongo_task_id'])

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        if 'mongo_task_id' not in kwargs:
            if self.name not in FAILED_TASK_BLACK_LIST:
                conn = pymysql.connect(host='10.10.180.145', user='hourong', passwd='hourong', db='Task',
                                       charset='utf8')
                with conn as cursor:
                    celery_task_id = task_id
                    task_id = kwargs.get('task_id', '')
                    kwargs.pop('task_id', None)
                    kwargs['local_ip'] = get_local_ip()
                    kwargs['u-time'] = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())
                    try:
                        cursor.execute(
                            'REPLACE INTO FailedTask(`id`, `task_id`, `args`, `kwargs`, error_info) VALUES (%s,%s,%s,%s,%s)',
                            (task_id, celery_task_id, str(args), json.dumps(kwargs), str(einfo)))
                    except Exception as e:
                        logger.exception(str(e))
                conn.close()
        else:
            celery_task_id = task_id
            task_id = kwargs.get('mongo_task_id', '')
            kwargs.pop('mongo_task_id', None)
            kwargs['local_ip'] = get_local_ip()
            kwargs['u-time'] = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())
            mongo_insert_failed_task(task_id, celery_task_id, args, kwargs, str(einfo))

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        task_source = get_source(self)
        task_type = get_type(self)
        r = redis.Redis(host='10.10.180.145', db=3)
        r.incr('|_||_|'.join([self.name, get_local_ip(), task_source, task_type, 'failure']))

        if 'mongo_task_id' not in kwargs:
            if self.name not in FAILED_TASK_BLACK_LIST:
                conn = pymysql.connect(host='10.10.180.145', user='hourong', passwd='hourong', db='Task',
                                       charset='utf8')
                with conn as cursor:
                    celery_task_id = task_id
                    task_id = kwargs.get('task_id', '')
                    kwargs.pop('task_id', None)
                    try:
                        cursor.execute(
                            'REPLACE INTO FailedTask(`id`, `task_id`, `args`, `kwargs`, error_info) VALUES (%s,%s,%s,%s,%s)',
                            (task_id, celery_task_id, str(args), json.dumps(kwargs), str(einfo)))
                    except Exception as exception:
                        logger.exception(str(exception.message))

                conn.close()
        else:
            celery_task_id = task_id
            task_id = kwargs.get('mongo_task_id', '')
            kwargs.pop('mongo_task_id', None)
            kwargs['local_ip'] = get_local_ip()
            kwargs['u-time'] = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())
            mongo_insert_failed_task(task_id, celery_task_id, args, kwargs, str(einfo))


if __name__ == '__main__':
    pass
