#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2017/9/26 下午5:18
# @Author  : Hou Rong
# @Site    : 
# @File    : poi_list_test.py
# @Software: PyCharm
from proj.my_lib.Common.Task import Task
from proj.total_tasks import poi_list_task

if __name__ == '__main__':
    # task = Task(_worker='', _task_id='demo', _source='daodao', _type='rest', _task_name='list_rest_daodao_20170925d',
    #             _used_times=0, max_retry_times=6,
    #             kwargs={'source': 'daodao',
    #                     'url': '/Tourism-g488103-Grand_Baie-Vacations.html',
    #                     'city_id': '51513',
    #                     'country_id': '409',
    #                     'poi_type': 'rest'})
    # poi_list_task(task=task)

    task = Task(_worker='', _task_id='demo', _source='daodao', _type='rest', _task_name='list_rest_daodao_20170925d',
                _used_times=0, max_retry_times=6,
                kwargs={
                    'source': 'daodao',
                    'url': '/Tourism-g294261-Cebu_Island_Visayas-Vacations.html',
                    'city_id': '20371',
                    'country_id': '107',
                    'poi_type': 'attr',
                    'check_in': '20171203',
                    'date_index': 0
                })
    poi_list_task(task=task)
