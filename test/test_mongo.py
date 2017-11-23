#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/22 上午10:03
# @Author  : Hou Rong
# @Site    : 
# @File    : test_mongo.py
# @Software: PyCharm
from __future__ import print_function
import pymongo

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['MongoTask']['City_Queue_poi_list_TaskName_city_total_qyer_20171120a']
# for line in collections.find({}):
#     if line['data_count']:
#         print(line['date_index'], line['data_count'])

# p = db.Programs.find_one({'Title':'...'})
#
# pipe = [
#         {'$match':{'_Program':DBRef('Programs',p['_id']),'Duration':{'$gt':0}}},
#         {'$group':{'_id':'$_Program', 'AverageDuration':{'$avg':'$Duration'}}}
#         ]
#
# eps = db.Episodes.aggregate(pipeline=pipe)
#
# print eps['result']

# for line in collections.aggregate([
#     {"$sample": {"size": "10"}}
# ]):
#     print(line)

FINISHED_ZERO_COUNT = 4

from collections import defaultdict

count_dict = defaultdict(int)
for line in collections.find({}):
    print(int(line['date_index']), len(set(list(map(lambda x: x[0], line['data_count'])))))
    count_dict[int(line['date_index']) == len(set(list(map(lambda x: x[0], line['data_count']))))] += 1
    # print(len(set(list(map(lambda x: x[0], line['data_count'])))))
    # print(all(map(lambda x: x == 0, list(filter(lambda x: x[-1], line['data_count']))[-FINISHED_ZERO_COUNT:])))
    # print(line['data_count'])
    # _count += 1
    # if _count == 10:
    #     break

    print(count_dict)
