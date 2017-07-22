#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/7/15 下午11:00
# @Author  : Hou Rong
# @Site    : 
# @File    : spider_init_by_mongo.py
# @Software: PyCharm
import os
from proj.celery import app
from proj.my_lib.task_module.mongo_task_func import get_task_total

if __name__ == '__main__':
    _count = 0
    for mongo_task_id, args in get_task_total(50000):
        _count += 1
        t_id = app.send_task('proj.file_downloader_task.file_downloader',
                             args=(args['source_url'], args['type'],
                                   os.path.join('/data/nfs/image/hotel_whole_site', args['mid']),),
                             kwargs={'mongo_task_id': mongo_task_id},
                             queue='file_downloader',
                             routing_key='file_downloader')
    print _count
