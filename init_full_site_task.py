#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/9 下午11:00
# @Author  : Hou Rong
# @Site    : 
# @File    : init_full_site_task.py
# @Software: PyCharm
import pymongo
import datetime

from proj.celery import app

client = pymongo.MongoClient(host='10.10.231.105')
collections = client['Task']['FullSite']

if __name__ == '__main__':
    kwargs = {}
    for line in collections.find().sort('select_time', 1).limit(10):
        _id = line['_id']
        mid = line['mid']
        website_url = line['website_url']
        collections.update(
            {'_id': _id},
            {
                '$set': {
                    'select_time': datetime.datetime.now()
                }
            }, upsert=False, multi=False)
        print(mid, website_url)
        app.send_task('proj.full_website_spider_task.full_site_spider',
                      args=(website_url, 0, website_url, {'id': mid},),
                      kwargs=kwargs,
                      queue='full_site_task',
                      routing_key='full_site_task')
