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
import proj.my_lib.Common.Browser
import types
from requests import ConnectionError, ConnectTimeout
from requests.adapters import SSLError, ProxyError
from urllib import quote
import json
from proj.my_lib.Common.KeyMatch import key_is_legal


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


def google_get_map_info(address):
    with proj.my_lib.Common.Browser.MySession(need_cache=True) as session:
        page = session.get('https://maps.googleapis.com/maps/api/geocode/json?address=' + quote(address))
        results = json.loads(page.text).get(
            'results', [])
        if len(results) == 0:
            return None
        map_info = results[0].get('geometry', {}).get('location', {})

        try:
            longitude = float(map_info.get('lng', None))
            latitude = float(map_info.get('lat', None))
        except Exception as e:
            print(e)
            return None
        return Coordinate(longitude, latitude)


if __name__ == '__main__':
    # print(get_md5('abc'))
    # print get_local_ip()
    # print(google_get_map_info('Plaza Soledad, 11, 06001 Badajoz, Spain'))
    print(google_get_map_info('3355 Las Vegas Blvd S'))
