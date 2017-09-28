#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/28 上午10:15
# @Author  : Hou Rong
# @Site    : 
# @File    : test_connection_pool.py
# @Software: PyCharm
from __future__ import print_function
import redis

connection_pool = redis.ConnectionPool(host='10.10.213.148', port=6379, db=0, max_connections=1)

if __name__ == '__main__':
    r1 = redis.Redis(connection_pool=connection_pool)
    r2 = redis.Redis(connection_pool=connection_pool)
    r3 = redis.Redis(connection_pool=connection_pool)

    print(r1.get('a'))
    print(r2.get('a'))
    print(r3.get('a'))
    print(r1)
    print(r2)
    print(r3)
