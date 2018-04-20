#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Created on 2017年2月16日

@author: dujun
"""
import functools
import traceback
import random
from mioji.common.pool import pool
from gevent.event import Event
from logger import logger
from greenlet import getcurrent

def block_async(pool, func, params):
    """
    通过 Event Lock 完成
    :param pool: 进程／线程／协程池
    :param func: 任务函数
    :param params: 可遍历项
    :return: 结果列表，由于被 task_wrapper 封装，返回值为 list [(res, is_data), ...]
    """
    result = []
    lock = Event()

    spider_taskinfo = None
    g = getcurrent()
    if hasattr(g,'spider_taskinfo'):
        spider_taskinfo = getcurrent().spider_taskinfo

    def callback(r):
        result.append(r)
        if len(result) == len(params):
            lock.set()

    for p in params:
        g = pool.apply_async(task_wrapper(func), p, callback=callback)
        g.spider_taskinfo = spider_taskinfo

    lock.wait()
    return result


def test(a):
    if a % 3 == 0:
        raise Exception('SS')
    time.sleep(random.randint(1, 3))
    return a, a


def task_wrapper(func):
    """
    apply_async 是在结果成功时调用 callback 中的函数，通过此方法将异常返回
    :param func: task 函数，例如：self.__single_crawl
    :return: 返回 函数结果 或 函数异常，以及为哪一者
    """

    @functools.wraps(func)
    def call(*args, **kwargs):
        try:
            return func(*args, **kwargs), True
        except Exception as exc:
            logger.exception('[新框架][页面解析异常][ {0} ]'.format(traceback.format_exc().replace('\n', '\t')))
            return (args, kwargs, exc), False

    return call


if __name__ == '__main__':
    import time

    start = time.time()
    res = block_async(pool, test, [(1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,)])
    print 'res:{0}'.format(res)
    print 'takes', time.time() - start
