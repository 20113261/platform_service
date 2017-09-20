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
from requests.adapters import SSLError, ProxyError
from Browser import MySession
from urllib import urlencode
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
        return str(self.longitude)+','+str(self.latitude)

def google_get_map_info(address):
    with MySession() as session:
        results = json.loads(session.get('https://maps.googleapis.com/maps/api/geocode/json?address='+urlencode(address))).get('results', [])
        if len(results)==0:return None
        map_info = results[0].get('geometry', {}).get('location', {})
        longitude = map_info.get('lng', None)
        latitude = map_info.get('lat', None)
        if not key_is_legal(longitude):return None
        if not key_is_legal(latitude): return None
        return Coordinate(longitude, latitude)

if __name__ == '__main__':
    print(get_md5('abc'))
    print get_local_ip()