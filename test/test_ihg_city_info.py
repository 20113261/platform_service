#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/12/19 下午2:25
# @Author  : Hou Rong
# @Site    : 
# @File    : test_ihg_city_info.py
# @Software: PyCharm
from proj.my_lib.Common.Task import Task
from proj.total_tasks import ihg_city_suggest

if __name__ == '__main__':
    args = {
        'keyword': 'Seoul'
    }
    task = Task(_worker='proj.total_tasks.ihg_city_suggest', _queue='supplement_field', _routine_key='supplement_field',
                _task_name='demo', _source='Ihg', _type='CityInfo', task_type=0, _used_times=0,
                max_retry_times=6, collection='Unknown', _task_id='demo', list_task_token='null', kwargs=args)

    # hotel_img_merge_task(task=task)
    ihg_city_suggest(task=task)
