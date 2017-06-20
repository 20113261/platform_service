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
from bson import Binary

DEFAULT_TASK_INFO_KEYS = ['source', 'source_id', 'city_id', 'url']


def save_task_and_page_content(task_name, content, *args, **kwargs):
    client = pymongo.MongoClient(host='10.10.231.105', port=27017)
    collection = client['PageSaver'][task_name]
    data = zlib.compress(content.encode('utf8'))
    kwargs['content'] = Binary(data)
    collection.save(kwargs)
    client.close()


def get_task_and_page_content(parent_task_id, task_name, **kwargs):
    start = time.time()
    client = pymongo.MongoClient(host='10.10.231.105', port=27017)
    collection = client['PageSaver'][task_name]
    res = collection.find_one({'task_id': parent_task_id})
    if 'task_info_keys' in kwargs:
        task_info_keys = kwargs['task_info_keys']
    else:
        task_info_keys = DEFAULT_TASK_INFO_KEYS

    result = {k: res[k] for k in task_info_keys}
    result['content'] = zlib.decompress(res['content']).decode()
    client.close()
    print 'Get Task Takes', time.time() - start
    return result


if __name__ == '__main__':
    print get_task_and_page_content('7ededbc01f00e0463f064e6ca9f8235f', 'hotel_base_data_170612')
