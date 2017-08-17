#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/15 上午11:37
# @Author  : Hou Rong
# @Site    : 
# @File    : Utils.py
# @Software: PyCharm
import hashlib
import socket
import traceback
from requests import ConnectionError, ConnectTimeout
from requests.adapters import SSLError


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    res = s.getsockname()[0]
    s.close()
    return res


def get_md5(string):
    return hashlib.md5(string).hexdigest()

def try3times(try_again_times=3, others_exptions=None):
    """用于任务中需要发小请求的，可以指定重试次数，添加兼容的异常"""
    def try_three(func):
        def try_(*args, **kwargs):
            for i in range(try_again_times):
                try:
                    return func(*args, **kwargs)
                except (SSLError, ConnectionError, ConnectTimeout, others_exptions) as e:
                    print traceback.format_exc(e)

        return try_
    return try_three

if __name__ == '__main__':
    print(get_md5('abc'))
    print get_local_ip()