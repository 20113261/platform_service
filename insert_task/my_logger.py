#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/25 上午9:30
# @Author  : Hou Rong
# @Site    :
# @File    : my_logger.py
# @Software: PyCharm
import os
import logging
import functools
import inspect
from datetime import datetime
from collections import defaultdict
from logging.handlers import RotatingFileHandler

log_path = "/data/log/service_platform"


class NamedRotatingFileHandler(RotatingFileHandler):
    def __init__(self, filename,path=None):
        if path:
            log_file = path
        else:
            log_file = log_path
        super(NamedRotatingFileHandler, self).__init__(
            filename=os.path.join(log_file, "{0}.log".format(filename)),
            maxBytes=100 * 1024 * 1024,
            backupCount=2
        )


def get_logger(logger_name,path=None):
    """
    初始化 logger get 可以获取到，为单例模式
    """
    if not path:
        if not os.path.exists(log_path):
            os.makedirs(log_path)
    else:
        if not os.path.exists(path):
            os.makedirs(path)

    # getLogger 为单例模式
    service_platform_logger = logging.getLogger(logger_name)
    service_platform_logger.setLevel(logging.DEBUG)
    datefmt = "%Y-%m-%d %H:%M:%S"
    file_log_format = "%(asctime)-15s %(threadName)s %(filename)s:%(lineno)d %(levelname)s:        %(message)s"
    formtter = logging.Formatter(file_log_format, datefmt)

    # handler 存在的判定
    if not service_platform_logger.handlers:
        # rotating file logger
        file_handle = NamedRotatingFileHandler(logger_name,path)

        file_handle.setFormatter(formtter)
        service_platform_logger.addHandler(file_handle)
        steam_handler = logging.StreamHandler()
        steam_handler.setFormatter(formtter)
        service_platform_logger.addHandler(steam_handler)

    return service_platform_logger


func_count_dict = defaultdict(int)
time_logger = get_logger('func_time_logger')


def func_time_logger(fun):
    @functools.wraps(fun)
    def logging(*args, **kw):
        try:
            func_file = inspect.getfile(fun)
        except Exception:
            func_file = ''
        func_name = fun.__name__
        func_key = (func_file, func_name)
        func_count_dict[func_key] += 1
        begin = datetime.now()
        result = fun(*args, **kw)
        end = datetime.now()
        time_logger.debug('[文件: {}][函数: {}][耗时 {}][当前运行 {} 个此函数]'.format(
            func_file, func_name, end - begin, func_count_dict[func_key]
        ))
        func_count_dict[func_key] -= 1
        return result

    return logging
