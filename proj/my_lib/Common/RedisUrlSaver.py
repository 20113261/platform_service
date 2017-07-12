#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/7 下午4:32
# @Author  : Hou Rong
# @Site    : 
# @File    : RedisUrlSaver.py
# @Software: PyCharm
import redis
import urlparse

ENOUGH_PAGE = 1000


class UrlSaver(object):
    def __init__(self):
        self.real_url = redis.Redis(host='10.10.213.148', db=14)
        self.unique_url = redis.Redis(host='10.10.213.148', db=15)

    @staticmethod
    def get_unique_url(url):
        url_parse_result = urlparse.urlparse(url)
        return url_parse_result.netloc + url_parse_result.path + '?' + '|'.join(
            urlparse.parse_qs(url_parse_result.query))

    def add_url(self, key, url):
        self.real_url.sadd(key, url)
        self.unique_url.sadd(key, self.get_unique_url(url))

    def has_crawled(self, key, url):
        return self.unique_url.sismember(key, self.get_unique_url(url))

    def crawled_enough(self, key):
        return self.unique_url.scard(key) > ENOUGH_PAGE


if __name__ == '__main__':
    us = UrlSaver()
    print us.has_crawled(u'http://www.castillosanfernando.org/',
                         u'http://www.castillosanfernando.org/visita-virtual-castell-sant-ferran?id=185&vsig1_0=6')

    print us.get_unique_url(
        'http://www.zg-nadbiskupija.hr/nadbiskupija/dokumenti/svetista-i-prostenista/nadbiskupija/default.aspx?id=7237&2=3&ijk=bbk')
