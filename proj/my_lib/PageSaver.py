#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/16 下午5:56
# @Author  : Hou Rong
# @Site    : 
# @File    : PageSaver.py
# @Software: PyCharm
import sys

reload(sys)
sys.setdefaultencoding('utf8')

import pymongo
import zlib
import time
import os
from bson import Binary

DEFAULT_TASK_INFO_KEYS = ['source', 'source_id', 'city_id', 'url']

client = pymongo.MongoClient(host='10.10.231.105', port=27017)


def save_task_and_page_content_old(task_name, content, *args, **kwargs):
    collection = client['PageSaver'][task_name]
    data = zlib.compress(content.encode('utf8'))
    kwargs['content'] = Binary(data)
    collection.save(kwargs)


def save_task_and_page_content(task_name, content, *args, **kwargs):
    collection = client['PageSaver'][task_name]
    data = zlib.compress(content.encode('utf8'))
    dir_path = os.path.join('/data/nfs/page_saver', task_name)
    if not os.path.exists(dir_path):
        os.mkdir(dir_path)
    f = open(os.path.join('/data/nfs/page_saver', task_name, kwargs['task_id']), 'wb')
    f.write(data)
    f.close()
    collection.save(kwargs)


def get_task_and_page_content(parent_task_id, task_name, **kwargs):
    start = time.time()
    collection = client['PageSaver'][task_name]
    res = collection.find_one({'task_id': parent_task_id})
    if 'task_info_keys' in kwargs:
        task_info_keys = kwargs['task_info_keys']
    else:
        task_info_keys = DEFAULT_TASK_INFO_KEYS

    result = {k: res[k] for k in task_info_keys}
    result['content'] = zlib.decompress(res['content']).decode()
    print 'Get Task Takes', time.time() - start
    return result


def generate_task_and_page_content(start_task_id, task_name, limit, **kwargs):
    start = time.time()
    collection = client['PageSaver'][task_name]
    if 'task_info_keys' in kwargs:
        task_info_keys = kwargs['task_info_keys']
    else:
        task_info_keys = DEFAULT_TASK_INFO_KEYS

    for each in collection.find({'task_id': {'$gte': start_task_id}}).sort("task_id").limit(limit):
        result = {k: each[k] for k in task_info_keys}
        result['content'] = zlib.decompress(each['content']).decode()
        yield result
    print 'Get {0} Tasks Takes {1}'.format(limit, time.time() - start)


if __name__ == '__main__':
    print get_task_and_page_content('7ededbc01f00e0463f064e6ca9f8235f', 'hotel_base_data_170612')
