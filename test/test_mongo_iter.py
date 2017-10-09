#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/9 下午7:13
# @Author  : Hou Rong
# @Site    : 
# @File    : test_mongo_iter.py
# @Software: PyCharm
import pymongo
import time

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['Test']['test2']
cursor = collections.find({})

if __name__ == '__main__':
    while True:
        _count = 2000
        while _count:
            _count -= 1
            try:
                line = cursor.next()
            except StopIteration:
                break
        print(time.time())
