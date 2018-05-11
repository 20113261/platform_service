#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/15 上午10:13
# @Author  : Hou Rong
# @Site    : 
# @File    : BaseSDK.py
# @Software: PyCharm
import json
import re
import redis
import logging
import pickle
import base64
import traceback
import pymongo
from proj.my_lib.Common.Task import Task, TaskType, TaskStatus
from proj.my_lib.logger import get_logger
from proj.my_lib.Common.Utils import get_local_ip
from proj.my_lib.task_module.mongo_task_func import update_task as mongo_update_task
from proj.my_lib.ServiceStandardError import ServiceStandardError
from proj.my_lib.task_module.mongo_task_func import update_city_list_task

FAILED_TASK_BLACK_LIST = {'proj.full_website_spider_task.full_site_spider'}

# 以下内容不进行重试，直接 finished 1
# 当为 0 正常
# 106 图片大于 10MB，107 图片因尺寸原因被过滤导致的问题
# 109 对方停业，入库过滤
# 29 对方的确无相关数据

DEFAULT_FINISHED_ERROR_CODE = [0, 106, 107, 109]

KnownTaskType = {
    "HotelList": "List",
    "Hotel": "Detail",
    "DownloadImages": "Images",
    "DaodaoListInfo": "List",
    "DaodaoDetail": "Detail",
    "QyerList": "List",
    "Qyerinfo": "Detail",
    "QyerDetail": "Detail",
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
        # 初始化任务
        self.task = task

        # 为任务设置 finished code
        self.finished_error_code = self.get_task_finished_code()
        self.task.task_finished_code = self.finished_error_code

        self.logger = get_logger(self.__class__.__name__)

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

    def get_task_finished_code(self):
        return DEFAULT_FINISHED_ERROR_CODE

    def on_success(self, ret_val):
        pass

    def on_failure(self, exc):
        pass

    def __task_report(self):
        r = redis.Redis(host='10.10.180.145', db=15)
        if self.task.error_code in self.finished_error_code:
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

        mongo_update_task(
            queue=self.task.queue,
            task_name=self.task.task_name,
            task_id=self.task.task_id,
            error_code=self.task.error_code
        )


    def _execute(self, **kwargs):
        pass

    def execute(self):
        try:
            # 任务真实执行函数
            res = self._execute(**self.task.kwargs)
            # 返回任务状态统计
            self.__task_report()
        except ServiceStandardError as exc:
            self.logger.exception(msg="[raise ServiceStandardError][code: {}][msg: {}]".format(
                exc.error_code,
                exc.msg
            ),
                exc_info=exc)
            # 如果其中有 wrapped exception 打印
            wrapped_exception = getattr(exc, 'wrapped_exception', None)
            if wrapped_exception:
                self.logger.error("[wrapped exception][error_code: {}][traceback: {}]".format(exc.error_code,
                                                                                              exc.wrapped_exception_info))
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

        # 当列表页任务时候，添加列表页城市相关信息
        if self.task.task_type == TaskType.LIST_TASK:
            self.update_city_list_info()
        return res

    def generate_city_collection_name(self):
        return 'City_Queue_{}_TaskName_{}'.format(self.task.queue, re.sub('list_', 'city_', self.task.task_name))

    def update_city_list_info(self):
        city_collection_name = self.generate_city_collection_name()

        task_result = False
        if self.task.status == TaskStatus.FINISHED:
            task_result = True

        # 更新城市列表任务返回结果
        update_city_list_task(
            city_collection_name=city_collection_name,
            list_task_token=self.task.list_task_token,
            data_count=(
                self.task.task_id,
                self.task.kwargs['date_index'],
                self.task.get_data_per_times,
                self.task.list_task_insert_db_count,
                self.task.used_times,
                task_result
            ),
            task_result=task_result
        )
