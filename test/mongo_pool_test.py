#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/28 下午2:40
# @Author  : Hou Rong
# @Site    : 
# @File    : mongo_pool_test.py
# @Software: PyCharm
import pymongo

client = pymongo.MongoClient(host='10.10.213.148', maxPoolSize=50, waitQueueMultiple=10)
