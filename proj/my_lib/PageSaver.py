#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/6/16 下午5:56
# @Author  : Hou Rong
# @Site    : 
# @File    : PageSaver.py
# @Software: PyCharm
import pymongo
import zlib
from bson import Binary


def save_task_and_page_content(task_name, content, *args, **kwargs):
    client = pymongo.MongoClient(host='10.10.231.105', port=27017)
    collection = client['PageSaver'][task_name]
    data = zlib.compress(content.encode('utf8'))
    kwargs['content'] = Binary(data)
    collection.save(kwargs)
