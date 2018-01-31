#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/1/24 下午8:05
# @Author  : Hou Rong
# @Site    : 
# @File    : test_google_drive_sdk.py
# @Software: PyCharm
import sys

sys.path.append('/data/lib')

from SDK.GoogleDriveSDK import GoogleDriveSDK
from proj.my_lib.Common.Task import Task

if __name__ == '__main__':
    # interCity Test
    # args = {
    #     'url': 'http://maps.google.cn/maps/api/directions/json?origin=42.6722,23.32854&destination=42.70141,23.324062&region=es&mode=driving&a1=10001&a2=10002&type=interCity'
    # }

    # innerCity transit Test
    args = {
        'url': 'http://maps.google.cn/maps/api/directions/json?origin=39.9339021,116.445898&destination=39.9330121,116.3705813&region=es&mode=transit&a1=va12345&a2=va12346&type=innerCity'
    }

    # innerCity driving Test
    # args = {
    #     'url': 'http://maps.google.cn/maps/api/directions/json?origin=42.6722,23.32854&destination=42.70141,23.324062&region=es&mode=driving&a1=va12345&a2=va12346&type=innerCity'
    # }

    # innerCity walking Test
    # args = {
    #     'url': 'http://maps.google.cn/maps/api/directions/json?origin=42.6722,23.32854&destination=42.70141,23.324062&region=es&mode=walking&a1=va12345&a2=va12346&type=innerCity'
    # }

    task = Task(_worker='proj.total_tasks.ihg_city_suggest', _queue='supplement_field', _routine_key='supplement_field',
                _task_name='demo', _source='Ihg', _type='CityInfo', task_type=0, _used_times=0,
                max_retry_times=6, collection='Unknown', _task_id='demo', list_task_token='null', kwargs=args)
    sdk = GoogleDriveSDK(task=task)
    sdk.execute()
