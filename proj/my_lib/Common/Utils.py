#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/15 上午11:37
# @Author  : Hou Rong
# @Site    : 
# @File    : Utils.py
# @Software: PyCharm
import sys

reload(sys)
sys.setdefaultencoding('utf8')
import hashlib
import socket
import traceback
import unittest
from requests import ConnectionError, ConnectTimeout
from requests.adapters import SSLError, ProxyError


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    res = s.getsockname()[0]
    s.close()
    return res


def get_md5(string):
    return hashlib.md5(string).hexdigest()


def has_chinese(str_or_unicode):
    if isinstance(str_or_unicode, str):
        string = str_or_unicode.decode()
    else:
        string = str_or_unicode

    return any(map(lambda c: u'\u4e00' <= c <= u'\u9fff', string))


def all_chinese(str_or_unicode):
    if isinstance(str_or_unicode, str):
        string = str_or_unicode.decode()
    else:
        string = str_or_unicode

    return all(map(lambda c: u'\u4e00' <= c <= u'\u9fff', string))


def try3times(try_again_times=3, others_exptions=None):
    """用于任务中需要发小请求的，可以指定重试次数，添加兼容的异常"""

    def try_three(func):
        def try_(*args, **kwargs):
            for i in range(try_again_times):
                try:
                    return func(*args, **kwargs)
                except (SSLError, ConnectionError, ConnectTimeout, ProxyError, others_exptions) as e:
                    print traceback.format_exc(e)

        return try_

    return try_three


class Coordinate:
    """赋值前请仔细确认，经度在前纬度在后"""

    def __init__(self, longitude, latitude):
        self.longitude = longitude
        self.latitude = latitude

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.longitude) + ',' + str(self.latitude)


class TestUtil(unittest.TestCase):
    def test_has_chinese(self):
        self.assertTrue(has_chinese('你好世界 Hello World'))
        self.assertFalse(has_chinese('Hello World'))

    def test_all_chinese(self):
        self.assertTrue(all_chinese(u"你好世界"))
        self.assertFalse(all_chinese(u"你好世界 asdfasdf"))


if __name__ == '__main__':
    # print(get_md5('abc'))
    # print get_local_ip()
    # print(google_get_map_info('Plaza Soledad, 11, 06001 Badajoz, Spain'))
    # print(google_get_map_info('3355 Las Vegas Blvd S'))
    unittest.main()
