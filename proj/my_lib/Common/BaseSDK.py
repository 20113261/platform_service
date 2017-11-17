#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/15 上午10:13
# @Author  : Hou Rong
# @Site    : 
# @File    : BaseSDK.py
# @Software: PyCharm
import json
import redis
import logging
import pickle
import base64
import traceback
from proj.my_lib.Common.Task import Task
from proj.my_lib.logger import get_logger
from proj.my_lib.Common.Utils import get_local_ip
from proj.my_lib.task_module.mongo_task_func import update_task as mongo_update_task
from proj.my_lib.ServiceStandardError import ServiceStandardError

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


class BaseSDK(object):
    def __init__(self, task, *args, **kwargs):
        """
        初始化抓取平台任务 SDK
        :type task: Task
        :param args:
        :param kwargs:
        """
        self.task = task
        self.logger = get_logger(__name__)

        # modify handler's formatter
        datefmt = "%Y-%m-%d %H:%M:%S"
        file_log_format = "%(asctime)-15s %(threadName)s %(filename)s:%(lineno)d %(levelname)s " \
                          "[source: {}][type: {}][task_id: {}]:        %(message)s".format(self.task.source,
                                                                                           self.task.type,
                                                                                           self.task.task_id)
        formtter = logging.Formatter(file_log_format, datefmt)
        for each_handler in self.logger.handlers:
            each_handler.setFormatter(formtter)
        self.logger.info("[init SDK]")

    def on_success(self, ret_val):
        pass

    def on_failure(self, exc):
        pass

    def __task_report(self):
        r = redis.Redis(host='10.10.180.145', db=15)
        if self.task.error_code in FINISHED_ERROR_CODE:
            finished = True
        else:
            finished = False

        r.incr('|_||_|'.join(
            map(lambda x: str(x),
                [self.task.worker, get_local_ip(), self.task.source, self.task.type, self.task.error_code,
                 self.task.task_name])))

        self.logger.debug('|_||_|'.join(
            map(lambda x: str(x),
                [self.task.worker, get_local_ip(), self.task.source, self.task.type, self.task.error_code,
                 self.task.task_name])))

        if finished:
            # todo 根据不同 task_name 分 collection
            mongo_update_task(self.task.task_id, 1)
        else:
            # todo 根据不同 task_name 分 collection
            mongo_update_task(self.task.task_id)

            # todo 保存任务最终状态
            # kwargs['local_ip'] = get_local_ip()
            # kwargs['u-time'] = time.strftime('%Y-%m-%d-%H-%M-%S', time.gmtime())

    def _execute(self, **kwargs):
        pass

    def execute(self):
        try:
            # 任务真实执行函数
            res = self._execute(**self.task.kwargs)
            # 返回任务状态统计
            self.__task_report()
        except ServiceStandardError as exc:
            self.logger.exception(msg="[raise ServiceStandardError]", exc_info=exc)
            # 如果其中有 wrapped exception 打印
            wrapped_exception = getattr(exc, 'wrapped_exception', None)
            if wrapped_exception:
                logging.exception(msg="[wrapped exception]", exc_info=wrapped_exception)
            # 更新任务中的错误码
            self.task.error_code = exc.error_code
            # 返回任务状态统计
            self.__task_report()
            res = traceback.format_exc()
        except Exception as exc:
            self.logger.exception(msg="[raise unknown error]", exc_info=exc)
            # 更新任务中的错误码
            self.task.error_code = 25
            # 返回任务状态统计
            self.__task_report()
            res = traceback.format_exc()
        return res
