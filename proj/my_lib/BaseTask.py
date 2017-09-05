# coding=utf-8
import redis
import time
import types
from celery.task import Task
from logger import get_logger

from proj.my_lib.Common.Utils import get_local_ip
from proj.my_lib.task_module.mongo_task_func import update_task as mongo_update_task
from proj.my_lib.task_module.routine_task_func import insert_failed_task as mongo_insert_failed_task

logger = get_logger('BaseTask')

FAILED_TASK_BLACK_LIST = {'proj.full_website_spider_task.full_site_spider'}


def get_str_type_object_attribute(obj, attr_name):
    if hasattr(obj, attr_name):
        attr_obj = getattr(obj, attr_name)
        if isinstance(attr_obj, types.StringTypes):
            return attr_obj
    return 'NULL'


def get_object_attribute(obj, attr_name):
    if hasattr(obj, attr_name):
        attr_obj = getattr(obj, attr_name)
        return str(attr_obj)
    return 'NULL'


def get_source(obj):
    return get_str_type_object_attribute(obj, 'task_source')


def get_type(obj):
    return get_str_type_object_attribute(obj, 'task_type')


def get_error_code(obj):
    return get_object_attribute(obj, 'error_code')


class BaseTask(Task):
    default_retry_delay = 1
    max_retries = 3

    def on_success(self, retval, task_id, args, kwargs):
        # 增加源以及抓取类型统计
        task_source = get_source(self)
        task_type = get_type(self)
        r = redis.Redis(host='10.10.180.145', db=15)
        error_code = get_error_code(self)
        if error_code == 'NULL':
            r.incr('|_||_|'.join(
                map(lambda x: str(x), [self.name, get_local_ip(), task_source, task_type, 103, 'success'])))
            logger.debug('|_||_|'.join(
                map(lambda x: str(x), [self.name, get_local_ip(), task_source, task_type, 103, 'success'])))
            finished = False
        else:
            if int(error_code) == 0:
                finished = True
            else:
                finished = False
            r.incr('|_||_|'.join(
                map(lambda x: str(x), [self.name, get_local_ip(), task_source, task_type, error_code, 'success'])))
            logger.debug('|_||_|'.join(
                map(lambda x: str(x), [self.name, get_local_ip(), task_source, task_type, error_code, 'success'])))

        if 'mongo_task_id' in kwargs:
            if finished:
                mongo_update_task(kwargs['mongo_task_id'], 1)
            else:
                mongo_update_task(kwargs['mongo_task_id'], 0)

            # 成功后记录成功内容
            celery_task_id = task_id
            task_id = kwargs.get('mongo_task_id', '')
            mongo_update_task(kwargs['mongo_task_id'], 0)
            kwargs.pop('mongo_task_id', None)
            kwargs['local_ip'] = get_local_ip()
            kwargs['u-time'] = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())
            mongo_insert_failed_task(task_id, celery_task_id, args, kwargs, retval, task_source, task_type,
                                     error_code)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        # 记录重试任务
        # if 'mongo_task_id' in kwargs:
        #     celery_task_id = task_id
        #     task_id = kwargs.get('mongo_task_id', '')
        #     kwargs.pop('mongo_task_id', None)
        #     kwargs['local_ip'] = get_local_ip()
        #     kwargs['u-time'] = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())
        #     einfo_i = str(einfo).find('Retry in')
        #     real_einfo = str(einfo)[einfo_i:] if einfo_i > -1 else str(einfo)
        #     mongo_insert_failed_task(task_id, celery_task_id, args, kwargs, real_einfo)
        pass

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        task_source = get_source(self)
        task_type = get_type(self)
        r = redis.Redis(host='10.10.180.145', db=15)
        error_code = get_error_code(self)
        # 防止抛异常且返回错误码 0 的情况
        if error_code in (0, '0'):
            error_code = 27

        # 更新任务统计
        if error_code == 'NULL':
            r.incr('|_||_|'.join(
                map(lambda x: str(x), [self.name, get_local_ip(), task_source, task_type, 103, 'failure'])))
            logger.debug('|_||_|'.join(
                map(lambda x: str(x), [self.name, get_local_ip(), task_source, task_type, 103, 'failure'])))
        else:
            r.incr('|_||_|'.join(
                map(lambda x: str(x), [self.name, get_local_ip(), task_source, task_type, error_code, 'failure'])))
            logger.debug('|_||_|'.join(
                map(lambda x: str(x), [self.name, get_local_ip(), task_source, task_type, error_code, 'failure'])))

        if 'mongo_task_id' in kwargs:
            # 更新任务状态
            mongo_update_task(kwargs['mongo_task_id'], 0)

            # 记录失败任务
            celery_task_id = task_id
            task_id = kwargs.get('mongo_task_id', '')
            mongo_update_task(kwargs['mongo_task_id'], 0)
            kwargs.pop('mongo_task_id', None)
            kwargs['local_ip'] = get_local_ip()
            kwargs['u-time'] = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())
            einfo_i = str(einfo).find('Retry in')
            real_einfo = str(einfo)[einfo_i:] if einfo_i > -1 else str(einfo)

            mongo_insert_failed_task(task_id, celery_task_id, args, kwargs, real_einfo, task_source, task_type,
                                     error_code)


if __name__ == '__main__':
    pass
