#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/11 下午7:19
# @Author  : Hou Rong
# @Site    : 
# @File    : test_qyer_city_info.py
# @Software: PyCharm
from proj.my_lib.Common.Task import Task
from proj.total_tasks import qyer_city_task

if __name__ == '__main__':
    args = {
        'keyword': '巴黎'
    }
    task = Task(_worker='proj.total_tasks.qyer_city_task', _queue='supplement_field', _routine_key='supplement_field',
                _task_name='demo', _source='Qyer', _type='CityInfo', task_type=0, _used_times=0,
                max_retry_times=6, collection='Unknown', _task_id='demo', list_task_token='null', kwargs=args)

    # hotel_img_merge_task(task=task)
    qyer_city_task(task=task)
