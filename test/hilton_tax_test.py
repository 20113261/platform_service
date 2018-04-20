#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/25 下午11:14
# @Author  : Hou Rong
# @Site    :
# @File    : qyer_list_test.py
# @Software: PyCharm
from proj.my_lib.Common.Task import Task
from proj.total_tasks import hilton_tax_task

if __name__ == '__main__':

    args = {
        "check_in": "20180128",
        "city_id": "50012",
        "source_id": "NYCDTDT",
        "source": "hilton",
        "date_index": 0
    }

    task = Task(_worker='', _task_id='demo', _source='hilton', _type='hotel_list', _task_name='hilton_tax_test',
                _used_times=0, max_retry_times=6,
                kwargs=args, _queue='hotel_list',
                _routine_key='hotel_list', list_task_token='test', task_type=0, collection='10.19.2.103')
    hilton_tax_task(task=task)
