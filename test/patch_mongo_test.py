#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/20 上午9:21
# @Author  : Hou Rong
# @Site    : 
# @File    : patch_mongo_test.py
# @Software: PyCharm
import mock
import proj.my_lib.my_mongo_insert

if __name__ == '__main__':
    import pymongo

    client = pymongo.MongoClient(host='10.10.231.105')
    collections = client['Test']['test2']
    data = [{
        'a': i
    } for i in range(20000)]

    with mock.patch('pymongo.collection.Collection._insert', proj.my_lib.my_mongo_insert.Collection._insert):
        result = collections.insert(data, continue_on_error=True)
    print(result)

