#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/16 下午4:43
# @Author  : Hou Rong
# @Site    : 
# @File    : total_tasks.py
# @Software: PyCharm
from __future__ import absolute_import
from SDK.PoiListSDK import PoiListSDK
from SDK.QyerListSDK import QyerListSDK
from SDK.HotelImgMergeSDK import HotelImgMergeSDK
from proj.celery import app
from proj.my_lib.BaseTask import BaseTask


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def qyer_list_task(self, task, **kwargs):
    _sdk = QyerListSDK(task=task)
    return _sdk.execute()


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def poi_list_task(self, task, **kwargs):
    _sdk = PoiListSDK(task=task)
    return _sdk.execute()


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='60/s')
def hotel_img_merge_task(self, task, **kwargs):
    _sdk = HotelImgMergeSDK(task=task)
    return _sdk.execute()
