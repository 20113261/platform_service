#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/8/25 上午9:30
# @Author  : Hou Rong
# @Site    : 
# @File    : logger.py
# @Software: PyCharm
import os
import logging
from logging.handlers import RotatingFileHandler

log_path = "/data/log/service_platform"


class NamedRotatingFileHandler(RotatingFileHandler):
    def __init__(self, filename):
        super(NamedRotatingFileHandler, self).__init__(
            filename=os.path.join(log_path, "{0}.log".format(filename)),
            maxBytes=100 * 1024 * 1024,
            backupCount=3
        )


def get_logger(logger_name):
    """
    初始化 logger get 可以获取到，为单例模式
    """
    if not os.path.exists(log_path):
        os.makedirs(log_path)
        os.mkdir(log_path)

    # getLogger 为单例模式
    api_logger = logging.getLogger(logger_name)
    api_logger.setLevel(logging.DEBUG)
    datefmt = "%Y-%m-%d %H:%M:%S"
    file_log_format = "%(asctime)-15s %(threadName)s %(filename)s:%(lineno)d %(levelname)s:        %(message)s"
    formtter = logging.Formatter(file_log_format, datefmt)

    # handler 存在的判定
    if not api_logger.handlers:
        # rotating file logger
        file_handle = NamedRotatingFileHandler(logger_name)
        file_handle.setFormatter(formtter)
        api_logger.addHandler(file_handle)
        steam_handler = logging.StreamHandler()
        api_logger.addHandler(steam_handler)

    return api_logger
