#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/25 下午10:30
# @Author  : Hou Rong
# @Site    : 
# @File    : qyer_detail_test.py
# @Software: PyCharm
from proj.my_lib.Common.Task import Task
from proj.total_tasks import qyer_detail_task

if __name__ == '__main__':
    task = Task(_worker='', _task_id='demo', _source='qyer', _type='poi_detail',
                _task_name='detail_total_qyer_20170929a',
                _used_times=0, max_retry_times=6,
                kwargs={'target_url': 'http://place.qyer.com/poi/V2UJYlFkBzVTbFI-/', 'city_id': 'TEST'})
    qyer_detail_task(task=task)
