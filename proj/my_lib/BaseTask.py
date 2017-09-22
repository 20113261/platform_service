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

KnownTaskType = {
    "HotelList": "List",
    "Hotel": "Detail",
    "DownloadImages": "Img",
    "Default": "Unknown"
}


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


def get_tag(kwargs):
    task_name = kwargs.get('task_name', '').split('')
    if len(task_name) != 4:
        return "NULL"
    else:
        return task_name[-1]


def get_report_type(task_type):
    return KnownTaskType.get(task_type, KnownTaskType["Default"])


def check_error_code(error_code, retry_count, task_tag, task_source, report_type, max_retry_times):
    report_r = redis.Redis(host='10.10.180.145', db=9)
    if int(error_code) == 0:
        # 当任务返回 0 时，代表任务成功
        if retry_count != 0:
            failed_key = "{0}|_|{1}|_|{2}|_|Failed".format(task_tag, task_source, report_type)
            report_r.decr(failed_key)

        report_key = "{0}|_|{1}|_|{2}|_|Done".format(task_tag, task_source, report_type)
        report_r.incr(report_key)
    else:
        # 标准错误统计
        if int(retry_count) == 0:
            report_key = "{0}|_|{1}|_|{2}|_|Failed".format(task_tag, task_source, report_type)
            report_r.incr(report_key)

        # 分错误码错误统计
        error_code_task_report_key = "{0}|_|{1}|_|{2}|_|Failed|_|{3}".format(task_tag, task_source, report_type,
                                                                             error_code)
        report_r.incr(error_code_task_report_key)


class BaseTask(Task):
    default_retry_delay = 1
    max_retries = 3

    def on_success(self, retval, task_id, args, kwargs):
        # 获取本批次任务，任务批次
        task_tag = get_tag(kwargs)

        # 获取当前任务重试次数
        retry_count = kwargs.get('retry_count', "NULL")
        max_retry_times = kwargs.get('max_retry_times', "NULL")

        # 增加源以及抓取类型统计
        task_source = get_source(self)
        task_type = get_type(self)
        r = redis.Redis(host='10.10.180.145', db=15)
        error_code = get_error_code(self)

        # 无错误码返回错误为 103
        if error_code == "NULL":
            error_code = 103

        # 流程统计入库
        if task_tag != 'NULL' and retry_count != 'NULL' and error_code != 'NULL' and max_retry_times != "NULL":
            report_type = get_report_type(task_type)
            # 入库任务进度以及分失败任务统计
            check_error_code(error_code, retry_count, task_tag, task_source, report_type, max_retry_times)

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
            # mongo_update_task(kwargs['mongo_task_id'], 0)
            kwargs.pop('mongo_task_id', None)
            kwargs['local_ip'] = get_local_ip()
            kwargs['u-time'] = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())

            # 暂时将返回信息保存到旧库中
            mongo_insert_failed_task(task_id, celery_task_id, args, kwargs, retval, task_source, task_type,
                                     error_code, is_routine_task=True)

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
        # 获取本批次任务，任务批次
        task_tag = get_tag(kwargs)

        task_source = get_source(self)
        task_type = get_type(self)
        r = redis.Redis(host='10.10.180.145', db=15)
        error_code = get_error_code(self)

        # 获取当前任务重试次数
        retry_count = kwargs.get('retry_count', "NULL")
        max_retry_times = kwargs.get('max_retry_times', "NULL")

        # 防止抛异常且返回错误码 0 的情况
        if error_code in (0, '0'):
            error_code = 27

        # 无错误码返回错误为 103
        if error_code == "NULL":
            error_code = 103

        if task_tag != 'NULL' and retry_count != 'NULL' and error_code != 'NULL' and max_retry_times != "NULL":
            report_type = get_report_type(task_type)
            # 入库任务进度以及分失败任务统计
            check_error_code(error_code, retry_count, task_tag, task_source, report_type, max_retry_times)

        # 更新任务统计
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

            # 当为 0 正常，106 图片大于 10MB，107 图片因尺寸原因被过滤导致的问题不进行重试，直接 finished 1
            if int(error_code) in [0, 106, 107]:
                mongo_update_task(kwargs['mongo_task_id'], 1)
            else:
                mongo_update_task(kwargs['mongo_task_id'], 0)

            kwargs.pop('mongo_task_id', None)
            kwargs['local_ip'] = get_local_ip()
            kwargs['u-time'] = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())
            einfo_i = str(einfo).find('Retry in')
            real_einfo = str(einfo)[einfo_i:] if einfo_i > -1 else str(einfo)

            # 暂时将返回错误信息保存到旧库中
            mongo_insert_failed_task(task_id, celery_task_id, args, kwargs, real_einfo, task_source, task_type,
                                     error_code, is_routine_task=True)


if __name__ == '__main__':
    pass
