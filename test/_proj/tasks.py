#coding:utf-8
# tasks.py
from __future__ import absolute_import
import os
import sys
import pdb

sys.path.remove('/usr/local/lib/python2.7/site-packages')
sys.path.insert(0,'/search/zhangxiaopeng/serviceplatoform/test')
from proj.celery import app

from celery import Celery, Task


import time

# app = Celery('proj',  backend='redis://10.10.180.145:6379/0', broker='redis://10.10.180.145:6379/0') #配置好celery的backend和broker

@app.task(bind=True)
def test_mes(self):
    for i in xrange(1, 11):
        print(i)
        time.sleep(1)
        self.update_state(state="PROGRESS", meta={'p': i*10})
    return 'finish'


# tasks.py
class MyTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        print('task done: {0}'.format(retval))
        return super(MyTask, self).on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        print('task fail, reason: {0}'.format(exc))
        return super(MyTask, self).on_failure(exc, task_id, args, kwargs, einfo)


@app.task(base=MyTask, name='proj.tasks.add')
def add(x, y):
    print(x+y)
    time.sleep(0.2)
    return x + y



# @app.on_after_configure.connect
# def setup_periodic_tasks(sender, **kwargs):
#     # Calls test('hello') every 10 seconds.
#     sender.add_periodic_task(10.0, add.s(1, 2), name='add every 10')
#
#     # Calls test('world') every 30 seconds
#     sender.add_periodic_task(30.0, add.s(2, 3), expires=10)
#
#     # Executes every Monday morning at 7:30 a.m.
#     sender.add_periodic_task(
#         crontab(hour=7, minute=30, day_of_week=1),
#         add.s(4, 5),
#     )

if __name__ == '__main__':
    # test_mes.delay()
    add.delay(2,2)
    print()