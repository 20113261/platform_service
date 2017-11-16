#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/16 下午4:43
# @Author  : Hou Rong
# @Site    : 
# @File    : total_tasks.py
# @Software: PyCharm
from __future__ import absolute_import
from SDK import *
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


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='8/s')
def hotel_list_task(self, task, **kwargs):
    _sdk = HotelListSDK(task=task)
    return _sdk.execute()


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='1/s')
def qyer_detail_task(self, task, **kwargs):
    _sdk = QyerDetailSDK(task=task)
    return _sdk.execute()


@app.task(bind=True, base=BaseTask, max_retries=3, rate_limit='2/s')
def poi_detail_task(self, task, **kwargs):
    _sdk = PoiDetailSDK(task=task)
    return _sdk.execute()


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='8/s')
def hotel_detail_task(self, task, **kwargs):
    _sdk = HotelDetailSDK(task=task)
    return _sdk.execute()


@app.task(bind=True, base=BaseTask, max_retries=2, rate_limit='13/s')
def images_task(self, task, **kwargs):
    _sdk = ImagesSDK(task=task)
    return _sdk.execute()