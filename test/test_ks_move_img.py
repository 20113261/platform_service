#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/12 下午8:02
# @Author  : Hou Rong
# @Site    : 
# @File    : test_ks_move_img.py
# @Software: PyCharm
from SDK import KsMoveSDK
from proj.my_lib.Common.Task import Task

if __name__ == '__main__':
    args = {
        'from_bucket': 'mioji-attr',
        'to_bucket': 'mioji-shop',
        'file_name': '00001b7e38457f1b826311b1ff92043c.jpg'
    }
    task = Task(_worker='proj.total_tasks.qyer_city_task', _queue='supplement_field',
                _routine_key='supplement_field',
                _task_name='demo', _source='Qyer', _type='CityInfo', task_type=0, _used_times=0,
                max_retry_times=6, collection='Unknown', _task_id='demo', list_task_token='null', kwargs=args)
    _sdk = KsMoveSDK(task=task)
    _sdk.execute()
