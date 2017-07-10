#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/7 下午4:32
# @Author  : Hou Rong
# @Site    : 
# @File    : RedisUrlSaver.py
# @Software: PyCharm
import redis


class UrlSaver(object):
    def __init__(self):
        self.r = redis.Redis(host='10.10.213.148', db=13)

    def add_url(self, key, url):
        self.r.sadd(key, url)

    def has_crawled(self, key, url):
        return self.r.sismember(key, url)


if __name__ == '__main__':
    us = UrlSaver()
    print us.has_crawled(u'http://www.castillosanfernando.org/',
                         u'http://www.castillosanfernando.org/visita-virtual-castell-sant-ferran?id=185&vsig1_0=6')
