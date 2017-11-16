#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/16 下午4:43
# @Author  : Hou Rong
# @Site    : 
# @File    : total_tasks.py
# @Software: PyCharm
from proj.celery import app
from proj.my_lib.BaseTask import BaseTask
from proj.qyer_list_task import QyerListSDK
from proj.poi_list_task import PoiListSDK


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def qyer_list_task(self, task, **kwargs):
    qyer_list_sdk = QyerListSDK(task=task)
    qyer_list_sdk.execute()


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def poi_list_task(self, task, **kwargs):
    poi_list_sdk = PoiListSDK(task=task)
    poi_list_sdk.execute()
