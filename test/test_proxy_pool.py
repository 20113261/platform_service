#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/28 下午4:17
# @Author  : Hou Rong
# @Site    : 
# @File    : test_proxy_pool.py
# @Software: PyCharm
from proj.my_lib.Common.ProxyPool import ProxyPool

if __name__ == '__main__':
    proxy_pool = ProxyPool()

    for i in range(200):
        print(proxy_pool.get_proxy('agoda'))
