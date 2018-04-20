#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2017年2月8日

@author: dujun
'''
import logging
import logging.config
from logging.handlers import SocketHandler, RotatingFileHandler

# 配置日志
FORMAT = "%(asctime)-15s %(threadName)s %(filename)s:%(lineno)d %(levelname)s %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"
formatter = logging.Formatter(FORMAT)
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

# # 设置handler
# console = logging.StreamHandler()
# console.setLevel(logging.DEBUG)
# console.setFormatter(formatter)

# 设置 socket stream handler
# socket_handler = SocketHandler('10.10.129.187', 7788)
formatter_good_look = logging.Formatter(FORMAT, datefmt)

# socket_handler.setFormatter(formatter_good_look)
# socket_handler.setLevel(logging.ERROR)


# 设置 rotating handler 不能设置，因为多进程

# 获得logger
logger = logging.getLogger('newframe')
# logger.addHandler(socket_handler)

# 禁用 ucloud的logger
ucloud_logger = logging.getLogger("UCLOUD")
ucloud_logger.setLevel(level=logging.CRITICAL)
# 禁用request的logger
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


