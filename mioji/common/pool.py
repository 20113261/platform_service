#!/usr/bin/python
# -*- coding: UTF-8 -*-

'''
Created on 2016年12月27日

@author: dujun
'''
import gevent
from gevent.pool import Pool
import time
import random
import functools


class TaskPool(Pool):
    def set_size(self, n=16):
        self._semaphore.counter = n
        self.size = n

    def grow(self, n=1):
        self._semaphore.counter += n
        self.size += n

    def shrink(self, n=1):
        self._semaphore.counter -= n
        self.size -= n

    # todo 增加自动调节协程池方法

    def apply_async(self, func, args=None, kwds=None, callback=None):
        return Pool.apply_async(self, func, args, kwds, callback)


pool = TaskPool(16)
new_pool = TaskPool(16)

# 用于抓取原始文件上传
file_upload_pool = Pool(512)


def task(i):
    sleep = random.randint(1, 3)
    time.sleep(sleep)
    if i % 3 == 0:
        raise Exception('ss')
    return [i], sleep


def task_done(*args, **kwargs):
    print '#' * 20
    err_or_data, is_data = args[0]
    print type(err_or_data), err_or_data
    print is_data


def task_wrapper(func):
    @functools.wraps(func)
    def call(*args, **kwargs):
        try:
            return func(*args, **kwargs), True
        except Exception as exc:
            return exc, False

    return call


if __name__ == '__main__':
    # test
    # group = []
    # for i in xrange(0, 23):
    #     pool.apply_async(task_wrapper(task), (i,), callback=task_done)
    #
    # pool.join()
    #
    # print 'All Task Finished'
    #
    # print pool.size

    group = []
    new_pool.set_size(30)
    for i in xrange(0, 23):
        group.append(new_pool.apply_async(task, (i,)))
    gevent.joinall(group)

    print 'All Task Finished'

    print new_pool.size
