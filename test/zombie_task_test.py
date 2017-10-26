#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/26 下午6:28
# @Author  : Hou Rong
# @Site    : 
# @File    : zombie_task_test.py
# @Software: PyCharm
import datetime
import pymongo

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['MongoTask']['Task']


def monitoring_zombies_task():
    try:
        cursor = collections.find(
            {'running': 1, 'utime': {'$lt': datetime.datetime.now() - datetime.timedelta(hours=1)}}, {'_id': 1},
            hint=[('running', 1), ('utime', -1)]).limit(
            5000)
        id_list = [id_dict['_id'] for id_dict in cursor]
        print(len(id_list))
        result = collections.update({
            '_id': {
                '$in': id_list
            }
        }, {
            '$set': {
                'finished': 0,
                'used_times': 0,
                'running': 0
            }
        }, multi=True)
        print(result)
    except Exception as e:
        print(e)


if __name__ == '__main__':
    monitoring_zombies_task()
