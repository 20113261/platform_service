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
        super(NamedRotatingFileHandler, self).__init__((os.path.join(log_path, "{0}.log".format(filename))))
        self.maxBytes = 100 * 1024 * 1024,
        self.backupCount = 3


def get_logger(logger_name):
    """
    初始化 短信服务的 logger 部分，无返回值，logger 的模式，可以随时get到
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
