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
import time
import requests
import json
import redis
import datetime
import functools
# import eventlet.greenpool
from requests import ConnectionError, ConnectTimeout
from requests.adapters import SSLError, ProxyError
from proj.my_lib.logger import get_logger

logger = get_logger("utils")

ip_save_logger = get_logger("ip_save_logger")
ip_saver_pool = redis.ConnectionPool(host='10.10.213.148', port=6379, db=0, max_connections=1)


# ip_saver_thread_pool = eventlet.greenpool.GreenPool(size=10)


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


def retry(times=3, raise_exc=True):
    def wrapper(func):
        @functools.wraps(func)
        def f(*args, **kwargs):
            _exc = None
            for i in range(times):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    _exc = exc
                    logger.exception(msg="[retry exception][func: {}][count: {}]".format(func.__name__, i),
                                     exc_info=exc)
            if _exc and raise_exc:
                raise _exc

        return f

    return wrapper


def try3times(try_again_times=3, others_exptions=None, final_raise_exception=False):
    """用于任务中需要发小请求的，可以指定重试次数，添加兼容的异常"""

    def try_three(func):
        def try_(*args, **kwargs):
            for i in range(try_again_times):
                try:
                    return func(*args, **kwargs)
                except (SSLError, ConnectionError, ConnectTimeout, ProxyError, others_exptions) as e:
                    print(traceback.format_exc(e))
            else:
                if final_raise_exception:
                    raise e

        return try_

    return try_three


class Coordinate:
    """赋值前请仔细确认，经度在前纬度在后"""

    def __init__(self, longitude='NULL', latitude='NULL'):
        self.longitude = longitude
        self.latitude = latitude

    def translate(self, value):
        """连接池 转义字段需要此方法"""
        return str(self.longitude) + ',' + str(self.latitude)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return str(self.longitude) + ',' + str(self.latitude)


def get_real_ip(targets, proxies):
    host, key = targets
    try:
        start = time.time()
        ip_page = requests.get(host, proxies=proxies, timeout=10)
        out_ip = json.loads(ip_page.text)[key]
        ip_save_logger.debug("[获取公网 ip 地址][ip: {0}][耗时: {1}]".format(out_ip, time.time() - start))
    except Exception as e:
        ip_save_logger.exception("[获取公网 ip 地址失败]", exc_info=e)
        return None
    return out_ip


def get_out_ip(proxies):
    out_ip = None
    for targets in [('http://httpbin.org/ip', 'origin'), ('https://api.ipify.org?format=json', 'ip')]:
        out_ip = get_real_ip(targets, proxies)
        if out_ip:
            break

    if out_ip:
        try:
            r = redis.Redis(connection_pool=ip_saver_pool)
            r.incr(datetime.datetime.now().strftime("ip_%Y_%m_%d_{0}".format(out_ip)))
        except Exception as e:
            ip_save_logger.exception("[ip 地址入 redis 失败]", exc_info=e)
            return False


# def get_out_ip_async(proxies):
#     ip_saver_thread_pool.spawn_n(get_out_ip, proxies)


class TestUtil(unittest.TestCase):
    def test_has_chinese(self):
        self.assertTrue(has_chinese('你好世界 Hello World'))
        self.assertFalse(has_chinese('Hello World'))

    def test_all_chinese(self):
        self.assertTrue(all_chinese(u"你好世界"))
        self.assertFalse(all_chinese(u"你好世界 asdfasdf"))


if __name__ == '__main__':
    pass
    # print(get_md5('abc'))
    # print get_local_ip()
    # print(google_get_map_info('Plaza Soledad, 11, 06001 Badajoz, Spain'))
    # print(google_get_map_info('3355 Las Vegas Blvd S'))
    # unittest.main()
    # p_r_o_x_y = '10.10.233.246:38530'
    # proxies = {
    #     'http': 'socks5://' + p_r_o_x_y,
    #     'https': 'socks5://' + p_r_o_x_y
    # }
    # print(get_out_ip_async(proxies))
    # while True:
    #     get_out_ip_async(proxies)
    #     time.sleep(1)
    #
    # @retry(times=5)
    # def exc():
    #     raise Exception()
    #
    # exc()
    # print("Hello World")
