#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/15 下午11:05
# @Author  : Hou Rong
# @Site    : 
# @File    : mongo_task_func.py
# @Software: PyCharm
import pymongo
import datetime

from bson import ObjectId

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['Task']['NewHotelTask']


def get_task_total(limit=30000):
    for line in collections.find({'finished': 0, "args.type": "img"}).sort('used_times', 1).sort('utime', 1).limit(
            limit):
        _id = line['_id']
        collections.update({
            '_id': _id
        }, {
            '$set': {
                'utime': datetime.datetime.now()
            },
            '$inc': {'used_times': 1}
        })
        yield _id, line['args']


def update_task(task_id):
    collections.update({
        '_id': ObjectId(task_id)
    }, {
        '$set': {
            "finished": 1
        }
    })


def get_per_task(task_id):
    return collections.find_one({'_id': ObjectId(task_id)})


if __name__ == '__main__':
    # for line in get_task_total(10):
    #     print line
    print update_task('596a3208e28b5414c164c3b1')
    # print get_per_task('596a3208e28b5414c164c3b1')
