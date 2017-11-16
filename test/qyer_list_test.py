#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/25 下午11:14
# @Author  : Hou Rong
# @Site    : 
# @File    : qyer_list_test.py
# @Software: PyCharm
from proj.my_lib.Common.Task import Task
from proj.qyer_list_task import qyer_list_task

if __name__ == '__main__':
    task = Task(_worker='', _task_id='demo', _source='qyer', _type='poi_list', _task_name='list_qyer_total_test',
                _used_times=0, max_retry_times=6,
                kwargs={'city_id': 'test', 'country_id': 'test', 'check_in': '20170925',
                        'city_url': 'http://place.qyer.com/st-augustine/'})
    qyer_list_task(task=task)
