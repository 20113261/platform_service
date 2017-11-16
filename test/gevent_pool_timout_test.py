#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/10/31 上午9:39
# @Author  : Hou Rong
# @Site    : 
# @File    : gevent_pool_timout_test.py
# @Software: PyCharm
import gevent.monkey

gevent.monkey.patch_all()
import gevent.pool
import time
import random

pool = gevent.pool.Pool(size=10)


def hello_world():
    t = random.randint(1, 10)
    time.sleep(t)
    print("Hello World, {}".format(t))


if __name__ == '__main__':
    for i in range(10):
        pool.apply_async(hello_world, ())
    pool.join(timeout=5)
