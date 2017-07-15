#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/15 上午11:56
# @Author  : Hou Rong
# @Site    : 
# @File    : RedisAlreadyDownload.py
# @Software: PyCharm

# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/7 下午4:32
# @Author  : Hou Rong
# @Site    :
# @File    : RedisUrlSaver.py
# @Software: PyCharm
import redis

ENOUGH_PAGE = 1000


class AlreadyDownload(object):
    def __init__(self):
        self.real_url = redis.Redis(host='10.10.114.35', db=13)

    def add_url(self, key, info):
        return self.real_url.set(key, info)

    def has_crawled(self, key):
        return self.real_url.exists(key)


if __name__ == '__main__':
    pass
