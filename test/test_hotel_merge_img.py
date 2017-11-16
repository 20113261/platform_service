#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/11/2 下午2:35
# @Author  : Hou Rong
# @Site    : 
# @File    : test_hotel_merge_img.py
# @Software: PyCharm
from proj.my_lib.Common.Task import Task
from proj.total_tasks import hotel_img_merge_task

if __name__ == '__main__':
    task = Task(_worker='', _task_id='demo', _source='qyer', _type='poi_list', _task_name='test_task',
                _used_times=0, max_retry_times=6,
                kwargs={'uid': 'ht21794341',
                        'min_pixels': '200000'})

    hotel_img_merge_task(task=task)
