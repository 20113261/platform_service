#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/28 下午8:59
# @Author  : Hou Rong
# @Site    : 
# @File    : test_new_mongo.py
# @Software: PyCharm
from mongo_pool import mongo_data_client

mongo_data_client['Test']['test'].save(
    {'text': 'hello-world'}
)
