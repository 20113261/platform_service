#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/16 下午8:43
# @Author  : Hou Rong
# @Site    : 
# @File    : MongoLog.py
# @Software: PyCharm
import pymongo

client = pymongo.MongoClient(host='10.10.231.105')


def save_log(log, mongo_task_id, collection_name):
    collections = client['Log'][collection_name]
    collections.save({
        'mongo_task_id': mongo_task_id,
        'log': log
    })
