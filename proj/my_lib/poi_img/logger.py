#!/usr/bin/env python
# coding=UTF8
"""
    @author: devin
    @time: 2013-11-12
    @desc:
"""
import logging.config

# 配置日志
FORMAT = "%(asctime)-15s %(threadName)s %(filename)s:%(lineno)d %(levelname)    s %(message)s"
logging.basicConfig(level=logging.ERROR, format=FORMAT)

logger = logging.getLogger('crawlLog')
logger.setLevel(logging.NOTSET)
