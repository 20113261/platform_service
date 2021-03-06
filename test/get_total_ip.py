#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/28 上午11:01
# @Author  : Hou Rong
# @Site    : 
# @File    : get_total_ip.py
# @Software: PyCharm
from __future__ import print_function
import redis
from collections import defaultdict

ip_saver_pool = redis.ConnectionPool(host='10.10.213.148', port=6379, db=0, max_connections=1)

if __name__ == '__main__':
    req_info = {}

    r = redis.Redis(connection_pool=ip_saver_pool)
    it = 0
    while True:
        it, res = r.scan(it, 'ip*')
        for each in res:
            req_info[each] = r.get(each)
        if it == 0:
            break

    for k, v in req_info.items():
        print(k, '=>', v)

    print("Total", len(req_info))
