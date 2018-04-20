#coding:utf-8
# trigger.py
from __future__ import absolute_import
import sys
import time

# sys.path=[]
sys.path.insert(0,'/usr/local/lib/python2.7/site-packages')

from tasks import add,test_mes
import sys

# def pm(body):
#     res = body.get('result')
#     if body.get('status') == 'PROGRESS':
#         sys.stdout.write('\r任务进度: {0}%'.format(res.get('p')))
#         sys.stdout.flush()
#     else:
#         print '\r'
#         print res
# r = test_mes.delay()
# print r.get(on_message=pm, propagate=False)

for i in range(1000):
    add.delay(i, i)
    # time.sleep(0.2)