#coding:utf-8
from __future__ import absolute_import
import os
import sys
import pdb

sys.path.insert(0,'/usr/local/lib/python2.7/site-packages')
# sys.modules.__delattr__('celery')
from celery import Celery, platforms


platforms.C_FORCE_ROOT = True

app = Celery('proj', include=['proj.tasks'])
app.config_from_object('proj.config')


if __name__ == '__main__':
    print()


