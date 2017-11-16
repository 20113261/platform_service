# coding=utf-8
import time
import types
import redis
from celery.signals import task_prerun
from celery.task import Task
from logger import get_logger
from proj.my_lib.Common.TaskResponse import TaskResponse
from proj.my_lib.Common.Utils import get_local_ip
from proj.my_lib.task_module.mongo_task_func import update_task as mongo_update_task
from proj.my_lib.task_module.routine_task_func import insert_failed_task as mongo_insert_failed_task

logger = get_logger('BaseTask')

FAILED_TASK_BLACK_LIST = {'proj.full_website_spider_task.full_site_spider'}

# 以下内容不进行重试，直接 finished 1
# 当为 0 正常
# 106 图片大于 10MB，107 图片因尺寸原因被过滤导致的问题
# 109 对方停业，入库过滤
# 29 对方的确无相关数据
FINISHED_ERROR_CODE = [0, 29, 106, 107, 109]

KnownTaskType = {
    "HotelList": "List",
    "Hotel": "Detail",
    "DownloadImages": "Images",
    "DaodaoListInfo": "List",
    "DaodaoDetail": "Detail",
    "QyerList": "List",
    "Qyerinfo": "Detail",
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
    task_name = kwargs.get('task_name', '').split('_')
    if len(task_name) != 4:
        return "NULL"
    else:
        return task_name[-1]


def get_report_type(task_type):
    return KnownTaskType.get(task_type, KnownTaskType["Default"])


def get_report_key(_task_name):
    _name_list = _task_name.split('_')
    if len(_name_list) == 4:
        _report_type, _crawl_type, _task_source, _task_tag = _name_list
        return _crawl_type.title(), _task_source.title(), _task_tag
    else:
        return None


def check_error_code(error_code, retry_count, task_tag, task_source, report_type, crawl_type, max_retry_times,
                     is_special=False):
    report_r = redis.Redis(host='10.10.180.145', db=9)
    if int(error_code) == 0:
        # 当任务返回 0 时，代表任务成功
        # 此时如果 Failed 已加 1 ，则减回去
        if retry_count != 0:
            failed_key = "{0}|_|{1}|_|{2}|_|{3}|_|Failed".format(task_tag, crawl_type, task_source, report_type)
            report_r.decr(failed_key)
            logger.debug("Decrease: {0}".format(failed_key))

        report_key = "{0}|_|{1}|_|{2}|_|{3}|_|Done".format(task_tag, crawl_type, task_source, report_type)
        report_r.incr(report_key)
        logger.debug("Increase: {0}".format(report_key))
    elif is_special:
        report_key = "{0}|_|{1}|_|{2}|_|{3}|_|FinalFailed".format(task_tag, crawl_type, task_source, report_type)
        report_r.incr(report_key)
        logger.debug("Increase: {0}".format(report_key))

        # 此时如果 Failed 已加 1 ，则减回去
        if retry_count != 0:
            failed_key = "{0}|_|{1}|_|{2}|_|{3}|_|Failed".format(task_tag, crawl_type, task_source, report_type)
            report_r.decr(failed_key)
            logger.debug("Decrease: {0}".format(failed_key))
    else:
        # 标准错误统计
        if int(retry_count) == 0:
            report_key = "{0}|_|{1}|_|{2}|_|{3}|_|Failed".format(task_tag, crawl_type, task_source, report_type)
            report_r.incr(report_key)
            logger.debug("Increase: {0}".format(report_key))
        elif int(retry_count) == int(max_retry_times):
            report_key = "{0}|_|{1}|_|{2}|_|{3}|_|FinalFailed".format(task_tag, crawl_type, task_source, report_type)
            report_r.incr(report_key)
            logger.debug("Increase: {0}".format(report_key))

            # 此时也应当减回去失败的内容
            failed_key = "{0}|_|{1}|_|{2}|_|{3}|_|Failed".format(task_tag, crawl_type, task_source, report_type)
            report_r.decr(failed_key)
            logger.debug("Decrease: {0}".format(failed_key))

        # 分错误码错误统计
        error_code_task_report_key = "{0}|_|{1}|_|{2}|_|{3}|_|Failed|_|{4}".format(task_tag, crawl_type, task_source,
                                                                                   report_type,
                                                                                   error_code)
        report_r.incr(error_code_task_report_key)
        logger.debug("Increase: {0}".format(error_code_task_report_key))


@task_prerun.connect
def task_sent_handler(task_id, task, *args, **kwargs):
    kw = kwargs['kwargs']
    kw['task_response'] = TaskResponse()


class BaseTask(Task):
    default_retry_delay = 1
    max_retries = 1

    def on_success(self, retval, task_id, args, kwargs):
        # 获取本批次任务，任务批次
        task_tag = get_tag(kwargs)

        # 获取当前任务重试次数
        retry_count = kwargs.get('retry_count', "NULL")
        max_retry_times = kwargs.get('max_retry_times', "NULL")

        # 增加源以及抓取类型统计
        task_response = kwargs['task_response']
        task_source = task_response.source
        task_type = task_response.type
        error_code = task_response.error_code

        # task_source = get_source(self)
        # task_type = get_type(self)
        # error_code = get_error_code(self)
        r = redis.Redis(host='10.10.180.145', db=15)

        # 无错误码返回错误为 103
        if error_code == "NULL":
            error_code = 103

        error_code = int(error_code)

        # 流程统计入库
        _key_list = get_report_key(kwargs.get('task_name', ''))
        if _key_list:
            _crawl_type, _task_source, _task_tag = _key_list
            report_type = get_report_type(task_type)
            check_error_code(
                error_code=error_code,
                retry_count=retry_count,
                task_tag=_task_tag,
                task_source=_task_source,
                report_type=report_type,
                crawl_type=_crawl_type,
                max_retry_times=max_retry_times
            )

        if int(error_code) in FINISHED_ERROR_CODE:
            finished = True
        else:
            finished = False
        r.incr('|_||_|'.join(
            map(lambda x: str(x),
                [self.name, get_local_ip(), task_source, task_type, error_code, kwargs.get('task_name', 'NULL')])))
        logger.debug('|_||_|'.join(
            map(lambda x: str(x),
                [self.name, get_local_ip(), task_source, task_type, error_code, kwargs.get('task_name', 'NULL')])))

        if 'mongo_task_id' in kwargs:
            if finished:
                mongo_update_task(kwargs['mongo_task_id'], 1)
            else:
                mongo_update_task(kwargs['mongo_task_id'])

            # 成功后记录成功内容
            celery_task_id = task_id
            task_id = kwargs.get('mongo_task_id', '')
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
        task_response = kwargs['task_response']
        task_source = task_response.source
        task_type = task_response.type
        error_code = task_response.error_code

        # task_source = get_source(self)
        # task_type = get_type(self)
        # error_code = get_error_code(self)
        r = redis.Redis(host='10.10.180.145', db=15)
        if error_code == 'NULL':
            error_code = get_error_code(exc)

        # 获取当前任务重试次数
        retry_count = kwargs.get('retry_count', "NULL")
        max_retry_times = kwargs.get('max_retry_times', "NULL")

        # 防止抛异常且返回错误码 0 的情况
        if error_code in (0, '0'):
            error_code = 27

        # 无错误码返回错误为 103
        if error_code == "NULL":
            error_code = 103

        error_code = int(error_code)

        # 更新任务统计
        start = time.time()
        r.incr('|_||_|'.join(
            map(lambda x: str(x),
                [self.name, get_local_ip(), task_source, task_type, error_code, kwargs.get('task_name', 'NULL')])))
        logger.debug('|_||_|'.join(
            map(lambda x: str(x),
                [self.name, get_local_ip(), task_source, task_type, error_code, kwargs.get('task_name', 'NULL')])))

        logger.debug("[single task report][takes: {}]".format(time.time() - start))

        special_type = False
        if 'mongo_task_id' in kwargs:
            # 记录失败任务
            celery_task_id = task_id
            task_id = kwargs.get('mongo_task_id', '')

            if int(error_code) in FINISHED_ERROR_CODE:
                special_type = True
                mongo_update_task(kwargs['mongo_task_id'], 1)
            else:
                mongo_update_task(kwargs['mongo_task_id'])

            kwargs.pop('mongo_task_id', None)
            kwargs['local_ip'] = get_local_ip()
            kwargs['u-time'] = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())
            einfo_i = str(einfo).find('Retry in')
            real_einfo = str(einfo)[einfo_i:] if einfo_i > -1 else str(einfo)

            # 暂时将返回错误信息保存到旧库中
            mongo_insert_failed_task(task_id, celery_task_id, args, kwargs, real_einfo, task_source, task_type,
                                     error_code, is_routine_task=True)

        # 流程统计入库
        start = time.time()
        _key_list = get_report_key(kwargs.get('task_name', ''))
        if _key_list:
            _crawl_type, _task_source, _task_tag = _key_list
            report_type = get_report_type(task_type)
            check_error_code(
                error_code=error_code,
                retry_count=retry_count,
                task_tag=_task_tag,
                task_source=_task_source,
                report_type=report_type,
                crawl_type=_crawl_type,
                max_retry_times=max_retry_times,
                is_special=special_type
            )
        logger.debug("[error code check report][takes: {}]".format(time.time() - start))


if __name__ == '__main__':
    pass
