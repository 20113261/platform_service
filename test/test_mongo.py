#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/22 上午10:03
# @Author  : Hou Rong
# @Site    : 
# @File    : test_mongo.py
# @Software: PyCharm
import pymongo

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['MongoTask']['City_Queue_poi_list_TaskName_city_total_qyer_20171120a']
for line in collections.find({}):
    if line['data_count']:
        print(line['date_index'], line['data_count'])
